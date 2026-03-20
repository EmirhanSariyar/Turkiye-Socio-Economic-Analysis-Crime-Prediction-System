# Final Roadmap

This file is a temporary internal planning note for completing the project.

Important:

- remove this file before the final public version of the repository

## 1. Data Quality

- review population, migration, and education coverage year by year
- expand historical education coverage if possible
- verify that province-year joins are correct after normalization
- inspect suspicious numeric fields and outliers one more time

## 2. Risk Definition

- finalize the primary justice-risk definition
- decide whether the final dashboard should emphasize:
  - investigation files opened
  - investigation files opened per 100k
  - yearly low / medium / high bands
- explain clearly that this is a justice proxy, not direct crime truth

## 3. Modeling

- keep both current baselines:
  - rich feature rate model
  - wide coverage flow model
- add clearer evaluation outputs
- consider confusion matrix and coefficient interpretation
- test whether a time-aware split improves the methodological story

## 4. Dashboard

- improve readability of the province snapshot table
- polish labels, number formatting, and explanatory text
- keep the current stable map for now
- revisit fully interactive map selection only in the final frontend polish stage

## 5. Final Frontend Revamp

- restore stronger interactivity only if it does not create rerun/fade issues
- improve the choropleth interaction model
- consider smoother province selection behavior
- improve the visual hierarchy of charts and top metrics

## 6. README Rewrite

- rewrite the README from scratch
- remove all starter-template language
- remove outdated sections such as:
  - `Suggested Data Sources`
  - old `Notes`
  - any wording that says the project is only a starter
- replace them with a professional project narrative based on the current state

New README should include:

- project overview
- problem statement
- dataset summary
- methodology
- model summary
- dashboard summary
- project structure
- setup and run instructions
- limitations
- future improvements

## 7. GitHub Cleanup

- add up-to-date screenshots
- align repository description with current project scope
- check file and folder names for consistency
- make sure only final-public docs remain

## 8. Final Demo Flow

- select a province and year
- show justice-risk level
- compare socio-economic indicators
- show trend over time
- explain why proxy-based interpretation matters

## Final Reminder

Before final publication:

- delete `docs/final_roadmap.md`
