# Refuge du Lac Blanc reservations monitor

Checks the HTML of https://refugelacblanc.com/en/ every 30 minutes using GitHub Actions. When the existing reservation badge stops displaying the known "closed" indicators, it sends **one** ntfy notification and disables the workflow.

The notification means the HTML status has **changed**, not that a reservation is guaranteed available. Website fetch errors, missing badges, missing text, or inconsistent badge labels fail safely without sending a false booking alert.

## Setup

1. Create a GitHub repository (a **private** repository avoids GitHub's 60-day public-repository inactivity disablement; check your monthly Actions minutes).
2. Add these files to its **default branch**, preserving `.github/workflows/check-reservations.yml`.
3. Install ntfy on your phone and subscribe to a long, hard-to-guess topic on `ntfy.sh`, e.g. `lac-blanc-<long-random-string>`.
4. In GitHub, open **Settings -> Secrets and variables -> Actions -> New repository secret** and add `NTFY_TOPIC_URL` set to `https://ntfy.sh/<your-random-topic>`.
5. Under **Actions -> Check Lac Blanc reservations -> Run workflow**, tick **test_notification** and manually trigger a run. Confirm your phone receives the test. A test will never disable the workflow.
6. Optionally run the workflow again without the test box checked to verify that it currently reports `closed`.

The scheduled workflow automatically checks every half-hour (UTC minute 17 and 47). Once the badge changes, it sends an ntfy alert with a link to the booking page and disables itself. To monitor a later season, manually re-enable the workflow in the Actions UI.

**Note:** Scheduled workflows in public GitHub repositories can be disabled after 60 days without repository activity; a private repo avoids this particular issue but uses your monthly included Actions compute quota. GitHub Actions schedules are best-effort and may occasionally be delayed or skipped. The page can also change its structure; if the action starts failing, inspect the logs and update the selectors.

## Local use

```bash
python -m pip install -r requirements.txt
python check_reservations.py
# To send a test notification:
NTFY_TOPIC_URL='https://ntfy.sh/<your-random-topic>' python check_reservations.py --test-notification
```
