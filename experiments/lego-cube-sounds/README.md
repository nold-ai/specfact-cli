# Lavawürfel-Synth

Eine eigenständige HTML-Seite (kein Build, keine Abhängigkeiten), die mit der
Rückkamera eines iPhones einen Lego-Würfel per Farbe verfolgt und daraus Klänge
macht.

Dieses Verzeichnis gehört **nicht** zum SpecFact-CLI-Produkt. Es ist ein
abgeschlossenes Spielzeug-Experiment auf Wunsch des Nutzers und wird von den
Produkt-Gates (OpenSpec, TDD, Modulsignaturen) nicht berührt.

## Benutzung

Die Seite braucht einen sicheren Kontext (`https://` oder `localhost`) —
Safari erlaubt `getUserMedia` nicht über `file://`.

Lokal am Rechner:

```bash
python3 -m http.server 8000 --directory experiments/lego-cube-sounds
# dann http://localhost:8000 öffnen
```

Am iPhone: die Datei über HTTPS ausliefern (z. B. als Claude-Artifact oder auf
einem eigenen Webspace) und den Link direkt in Safari öffnen — nicht in einem
eingebetteten Fenster, sonst blockiert iOS den Kamerazugriff.

## Ablauf

1. **Kamera starten** antippen und Zugriff erlauben.
2. Den Würfel in das orange Zielquadrat halten und **Farbe merken** drücken.
   Die App speichert die Chromatizität (`r/(r+g+b)`, `g/(r+g+b)`) der farbigen,
   hellen Bildpunkte im Zielfeld — schwarze Flächen und Schatten werden dabei
   ausgeschlossen.
3. Bewegen, drehen, näher holen.

## Zuordnung Bewegung → Klang

| Eingabe                        | Klang                                              |
| ------------------------------ | -------------------------------------------------- |
| Links/rechts                   | Tonhöhe, auf eine Moll-Pentatonik gerastert         |
| Hoch/runter                    | Filter-Grenzfrequenz (oben = heller)                |
| Näher zur Kamera (größer)      | Lautstärke plus Sub-Sinus eine Oktave tiefer        |
| Schneller Ruck                 | kurzer Stein-Klack (gefilterter Rauschimpuls)       |
| Drehen (Flächensprung)         | Wusch nach unten bzw. oben                          |
| Ruhig im Bild                  | vereinzelte Lava-Blasen                             |
| Würfel verschwindet            | Klang blendet aus                                   |

Ohne Kalibrierung läuft die App im **Bewegungsmodus**: Bilddifferenz über das
ganze Bild steuert Tonhöhe und Lautstärke.

## Technik

- Analyse auf einem 160 px breiten Offscreen-Canvas, damit jedes Videobild in
  einem `requestAnimationFrame`-Durchlauf verarbeitet werden kann.
- Farbabgleich über normalisierte Chromatizität statt roher RGB-Distanz, damit
  Helligkeitsschwankungen den Treffer nicht zerstören.
- Web Audio: ein Sägezahn durch ein Tiefpassfilter, ein Sub-Sinus, ein
  Rausch-Teppich und kurze Impulse für Klacks und Blasen.
- `AudioContext` wird erst in der Nutzergeste erzeugt und beim Wechsel in den
  Hintergrund angehalten (iOS-Anforderungen).
