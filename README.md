# Designveloper Social Data Skills

Public Hermes skills for Google Trends, technology news, competitor content, Facebook traffic, and X traffic. Installed copies run from Hermes persistent storage; GitHub is not required during normal execution.

## Install

```bash
hermes skills tap add designveloper/social-data-skills
hermes skills install designveloper/social-data-skills/skills/google-trends-sync --yes
hermes skills install designveloper/social-data-skills/skills/tech-news-sync --yes
hermes skills install designveloper/social-data-skills/skills/competitor-content-sync --yes
hermes skills install designveloper/social-data-skills/skills/facebook-traffic-sync --yes
hermes skills install designveloper/social-data-skills/skills/x-traffic-sync --yes
```

Verify the five skills before creating jobs. Create a default job only when its stable name is absent:

```bash
hermes cron create "0 9 * * *" "Fetch and update Google Trends now. Follow the google-trends-sync skill." --name "Update Google Trends" --skill google-trends-sync --deliver local
hermes cron create "0 * * * *" "Fetch and update technology news now. Follow the tech-news-sync skill." --name "Update Tech News" --skill tech-news-sync --deliver local
hermes cron create "0 9 * * *" "Fetch and update competitor content now. Follow the competitor-content-sync skill." --name "Update Competitor Content" --skill competitor-content-sync --deliver local
hermes cron create "0 9 * * *" "Fetch and update Facebook traffic now. Follow the facebook-traffic-sync skill." --name "Update Facebook Traffic" --skill facebook-traffic-sync --deliver local
hermes cron create "0 9 * * *" "Fetch and update X traffic now. Follow the x-traffic-sync skill." --name "Update X Traffic" --skill x-traffic-sync --deliver local
```

Do not recreate an existing stable job; preserve operator schedule, pause, prompt, and delivery changes.

## Update

```bash
hermes skills update google-trends-sync
hermes skills update tech-news-sync
hermes skills update competitor-content-sync
hermes skills update facebook-traffic-sync
hermes skills update x-traffic-sync
```

Updating skills never resets cron jobs.
