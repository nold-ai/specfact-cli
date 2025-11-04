# Deviation Report

**Manual Plan**: manual
**Auto Plan**: auto-derived
**Total Deviations**: 28


## Deviations by Type

### mismatch (6 issues)

- **LOW**: Idea title differs: manual='SpecFact CLI', auto='Unknown  Project'
  - Location: `idea.title`
  - Fix: Update auto plan title to match manual plan

- **LOW**: Idea narrative differs between plans
  - Location: `idea.narrative`
  - Fix: Update narrative to match manual plan

- **LOW**: Product theme 'Contract Validation' in manual plan but not in auto plan
  - Location: `product.themes`
  - Fix: Add theme 'Contract Validation' to auto plan

- **LOW**: Product theme 'Plan Management' in manual plan but not in auto plan
  - Location: `product.themes`
  - Fix: Add theme 'Plan Management' to auto plan

- **LOW**: Product theme 'Code Analysis' in manual plan but not in auto plan
  - Location: `product.themes`
  - Fix: Add theme 'Code Analysis' to auto plan

- **LOW**: Product theme 'Validation' in auto plan but not in manual plan
  - Location: `product.themes`
  - Fix: Remove theme 'Validation' from auto plan or add to manual

### missing_feature (5 issues)

- **HIGH**: Feature 'FEATURE-CLI' (CLI Framework) in manual plan but not implemented
  - Location: `features[FEATURE-CLI]`
  - Fix: Implement feature 'FEATURE-CLI' or update manual plan

- **HIGH**: Feature 'FEATURE-PLAN' (Plan Management) in manual plan but not implemented
  - Location: `features[FEATURE-PLAN]`
  - Fix: Implement feature 'FEATURE-PLAN' or update manual plan

- **HIGH**: Feature 'FEATURE-ANALYZE' (Code Analysis) in manual plan but not implemented
  - Location: `features[FEATURE-ANALYZE]`
  - Fix: Implement feature 'FEATURE-ANALYZE' or update manual plan

- **HIGH**: Feature 'FEATURE-VALIDATORS' (Validation Framework) in manual plan but not implemented
  - Location: `features[FEATURE-VALIDATORS]`
  - Fix: Implement feature 'FEATURE-VALIDATORS' or update manual plan

- **HIGH**: Feature 'FEATURE-GENERATORS' (Code Generators) in manual plan but not implemented
  - Location: `features[FEATURE-GENERATORS]`
  - Fix: Implement feature 'FEATURE-GENERATORS' or update manual plan

### extra_implementation (17 issues)

- **MEDIUM**: Feature 'FEATURE-CONTRACTMIGRATIONHELPER' (Contract Migration Helper) found in code but not in manual plan
  - Location: `features[FEATURE-CONTRACTMIGRATIONHELPER]`
  - Fix: Add feature 'FEATURE-CONTRACTMIGRATIONHELPER' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-CONTRACTFIRSTTESTMANAGER' (Contract First Test Manager) found in code but not in manual plan
  - Location: `features[FEATURE-CONTRACTFIRSTTESTMANAGER]`
  - Fix: Add feature 'FEATURE-CONTRACTFIRSTTESTMANAGER' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-SMARTCOVERAGEMANAGER' (Smart Coverage Manager) found in code but not in manual plan
  - Location: `features[FEATURE-SMARTCOVERAGEMANAGER]`
  - Fix: Add feature 'FEATURE-SMARTCOVERAGEMANAGER' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-YAMLUTILS' (Y A M L Utils) found in code but not in manual plan
  - Location: `features[FEATURE-YAMLUTILS]`
  - Fix: Add feature 'FEATURE-YAMLUTILS' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-GITOPERATIONS' (Git Operations) found in code but not in manual plan
  - Location: `features[FEATURE-GITOPERATIONS]`
  - Fix: Add feature 'FEATURE-GITOPERATIONS' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-FSMVALIDATOR' (F S M Validator) found in code but not in manual plan
  - Location: `features[FEATURE-FSMVALIDATOR]`
  - Fix: Add feature 'FEATURE-FSMVALIDATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-SCHEMAVALIDATOR' (Schema Validator) found in code but not in manual plan
  - Location: `features[FEATURE-SCHEMAVALIDATOR]`
  - Fix: Add feature 'FEATURE-SCHEMAVALIDATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-PLANCOMPARATOR' (Plan Comparator) found in code but not in manual plan
  - Location: `features[FEATURE-PLANCOMPARATOR]`
  - Fix: Add feature 'FEATURE-PLANCOMPARATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-CODEANALYZER' (Code Analyzer) found in code but not in manual plan
  - Location: `features[FEATURE-CODEANALYZER]`
  - Fix: Add feature 'FEATURE-CODEANALYZER' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-PROTOCOLGENERATOR' (Protocol Generator) found in code but not in manual plan
  - Location: `features[FEATURE-PROTOCOLGENERATOR]`
  - Fix: Add feature 'FEATURE-PROTOCOLGENERATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-PLANGENERATOR' (Plan Generator) found in code but not in manual plan
  - Location: `features[FEATURE-PLANGENERATOR]`
  - Fix: Add feature 'FEATURE-PLANGENERATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-REPORTGENERATOR' (Report Generator) found in code but not in manual plan
  - Location: `features[FEATURE-REPORTGENERATOR]`
  - Fix: Add feature 'FEATURE-REPORTGENERATOR' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-DEVIATIONREPORT' (Deviation Report) found in code but not in manual plan
  - Location: `features[FEATURE-DEVIATIONREPORT]`
  - Fix: Add feature 'FEATURE-DEVIATIONREPORT' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-VALIDATIONREPORT' (Validation Report) found in code but not in manual plan
  - Location: `features[FEATURE-VALIDATIONREPORT]`
  - Fix: Add feature 'FEATURE-VALIDATIONREPORT' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-TEXTUTILS' (Text Utils) found in code but not in manual plan
  - Location: `features[FEATURE-TEXTUTILS]`
  - Fix: Add feature 'FEATURE-TEXTUTILS' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-MESSAGEFLOWFORMATTER' (Message Flow Formatter) found in code but not in manual plan
  - Location: `features[FEATURE-MESSAGEFLOWFORMATTER]`
  - Fix: Add feature 'FEATURE-MESSAGEFLOWFORMATTER' to manual plan or remove from code

- **MEDIUM**: Feature 'FEATURE-LOGGERSETUP' (Logger Setup) found in code but not in manual plan
  - Location: `features[FEATURE-LOGGERSETUP]`
  - Fix: Add feature 'FEATURE-LOGGERSETUP' to manual plan or remove from code
