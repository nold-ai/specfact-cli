# frozen_string_literal: true

# Execute with the frozen docs bundle. Fixtures and output stay in a temporary
# directory; generated JavaScript is inspected as text and never executed.
require "jekyll"
require "jekyll-redirect-from"
require "jekyll-feed"
require "rexml/document"
require "tmpdir"
require "fileutils"
require "json"
require "yaml"

module JekyllDependencyChecks
  SITE_URL = "https://docs.example.test"

  def self.assert(condition, message)
    raise message unless condition
  end

  def self.write_page(source, name, data, content = "Original content")
    path = File.join(source, name)
    FileUtils.mkdir_p(File.dirname(path))
    File.write(path, "#{YAML.dump(data)}---\n#{content}\n")
  end

  def self.build_site(source, destination, baseurl, plugins)
    config = Jekyll.configuration(
      "source" => source, "destination" => destination, "url" => SITE_URL,
      "baseurl" => baseurl, "plugins" => plugins, "quiet" => true,
      "timezone" => "UTC", "title" => "Dependency probes"
    )
    site = Jekyll::Site.new(config)
    Dir.chdir(source) { site.process }
    site
  end

  def self.redirect(baseurl)
    Dir.mktmpdir("jekyll-redirect-probe") do |source|
      destination = File.join(source, "_site")
      write_page(source, "target.md", {"permalink" => "/target/", "redirect_from" => "/legacy/"})
      write_page(source, "external.md", {"permalink" => "/external/", "redirect_to" => "https://example.test/safe?a=1&b=2"})
      rejected = ["javascript:alert(1)", "data:text/html,probe"]
      rejected.each_with_index do |target, index|
        write_page(source, "blocked-#{index}.md", {"permalink" => "/blocked-#{index}/", "redirect_to" => target})
      end
      payload = 'https://example.test/"</script><img src=x>`{probe}?a=1&b=2'
      write_page(source, "encoded.md", {"permalink" => "/encoded/", "redirect_to" => payload})
      build_site(source, destination, baseurl, ["jekyll-redirect-from"])
      rejected.each_index do |index|
        output = File.read(File.join(destination, "blocked-#{index}/index.html"))
        assert(output.include?("Original content") && !output.include?("<script>location="), "Disallowed redirect scheme was rendered: #{index}")
      end
      write_page(source, "normalized.md", {"permalink" => "/normalized/", "redirect_to" => "\u0001java\tscript:alert(1)"})
      build_site(source, destination, baseurl, ["jekyll-redirect-from"])
      assert(File.read(File.join(destination, "normalized/index.html")).include?("Original content"), "Browser-normalized scheme was rendered")
      redirects = JSON.parse(File.read(File.join(destination, "redirects.json")))
      assert(redirects["/legacy/"] == "#{SITE_URL}#{baseurl}/target/", "Ordinary redirect lost URL/baseurl")
      external = File.read(File.join(destination, "external/index.html"))
      assert(external.include?("a=1&amp;b=2"), "Redirect HTML attribute was not escaped")
      encoded = File.read(File.join(destination, "encoded/index.html"))
      target = JSON.parse(encoded.match(%r!<script>location=(.*?)</script>!m)[1])
      assert(target.include?("%22%3C/script%3E%3Cimg%20src=x%3E%60%7Bprobe%7D"), "Unsafe redirect characters were not encoded")
      assert(!encoded.include?("<img src=x>"), "Redirect target escaped into HTML")
    end
    puts "PASS redirect security and ordinary URLs: baseurl=#{baseurl.inspect}"
  end

  def self.feed_language(baseurl)
    Dir.mktmpdir("jekyll-feed-language-probe") do |source|
      destination = File.join(source, "_site")
      lang = 'en" probe="injected'
      File.write(File.join(source, "_config.yml"), YAML.dump({"lang" => lang}))
      write_page(source, "_posts/2026-10-01-probe.html", {"title" => "Probe", "lang" => lang}, "<p>ordinary content</p>")
      build_site(source, destination, baseurl, ["jekyll-feed"])
      root = REXML::Document.new(File.read(File.join(destination, "feed.xml"))).root
      assert(root.attributes["xml:lang"] == lang && !root.attributes["probe"], "Feed language injected an XML attribute")
      entry = root.elements["entry"]
      assert(entry.attributes["xml:lang"] == lang && !entry.attributes["probe"], "Post language injected an XML attribute")
      alternate = root.elements.to_a("link").find { |link| link.attributes["rel"] == "alternate" }
      assert(alternate.attributes["hreflang"] == lang && !alternate.attributes["probe"], "Alternate language was not escaped")
      assert(alternate.attributes["href"] == "#{SITE_URL}#{baseurl}/", "Feed URL lost deployment baseurl")
    end
    puts "PASS feed language escaping and ordinary URLs: baseurl=#{baseurl.inspect}"
  end

  def self.feed_cdata(baseurl)
    Dir.mktmpdir("jekyll-feed-cdata-probe") do |source|
      destination = File.join(source, "_site")
      payload = "before]]>after"
      write_page(source, "_posts/2026-10-01-probe.html", {"title" => "Probe", "description" => payload}, "<p>#{payload}</p>")
      build_site(source, destination, baseurl, ["jekyll-feed"])
      entry = REXML::Document.new(File.read(File.join(destination, "feed.xml"))).root.elements["entry"]
      assert(entry.elements["content"].texts.map(&:value).join == "<p>#{payload}</p>", "Content CDATA did not preserve text")
      assert(entry.elements["summary"].texts.map(&:value).join == payload, "Summary CDATA did not preserve text")
    end
    puts "PASS feed content and summary CDATA: baseurl=#{baseurl.inspect}"
  end

end

modes = ARGV.empty? ? ["redirect", "feed_language", "feed_cdata"] : ARGV
abort "Unknown dependency probe" unless (modes - %w[redirect feed_language feed_cdata]).empty?
["", "/preview"].each do |baseurl|
  modes.each { |mode| JekyllDependencyChecks.public_send(mode, baseurl) }
end
puts "Validated Jekyll #{Jekyll::VERSION}, JSON #{JSON::VERSION}, redirect #{JekyllRedirectFrom::VERSION}, feed #{Gem.loaded_specs.fetch("jekyll-feed").version}"
