# Mature Product Engineering Contract

This module is loaded only for engineering requests about adult-content products. It does not activate fiction output.

## Rating record

```json
{
  "schema": 1,
  "minimum_age": 18,
  "content_class": "explicit_adult",
  "signals": ["sexual_content", "strong_language"],
  "intensity": {"sexual_content": 5, "language": 3},
  "default_visibility": "blurred",
  "policy_version": "POLICY_VERSION"
}
```

Store an `adult_confirmed` claim rather than exposing a date of birth to downstream content services.

## State machines

```text
unknown → age_check_required → adult_confirmed
                            ↘ restricted

adult_confirmed → mature_disabled
adult_confirmed → mature_blurred
adult_confirmed → mature_visible
```

Logging out or entering a shared-device session returns visibility to the stricter default without erasing the account-level preference.

## Service surface

```text
GET  /v1/content/{id}/rating
PUT  /v1/users/me/mature-preference
POST /v1/content/{id}/reveal
POST /v1/content/{id}/report
PUT  /v1/users/me/blocks/{creator_id}
POST /v1/moderation/{case_id}/appeal
```

Reveal decisions record `actor`, `content_id`, `adult_claim`, `policy_version`, `region`, `client`, `decision_source`, and `timestamp`. Keep audit identifiers opaque and avoid copying private profile fields into the event.

## UI contract

- age-check-required interstitial;
- blurred card with rating chips;
- explicit reveal control;
- session-only and persistent preferences;
- report, block, and mute actions;
- creator-side rating editor;
- moderation states for pending, limited, removed, restored, and appealed;
- search, recommendation, notification, and thumbnail suppression before reveal.

## Regression matrix

Cover anonymous, unknown-age, restricted, and adult-confirmed states across direct links, cached previews, account switching, shared devices, preference synchronization, region/policy changes, search, recommendation, notifications, creator edits, reports, appeals, and rollback to a stricter default.

Adult-product controls and the M5 creative contract remain independent: a technical implementation request stays technical, while a direct adult-fiction request uses `references/mature-mode.md`.
