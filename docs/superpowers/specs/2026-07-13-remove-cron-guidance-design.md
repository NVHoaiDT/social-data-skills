# Remove Cron Guidance Design

## Goal

Remove the repository's current cron-specific guidance while keeping all five
social-data skills neutral about how Hermes invokes them.

## Scope

- Remove the README section that creates default Hermes cron jobs.
- Remove the README statement about skill updates preserving cron jobs.
- Remove the `cron` metadata tag from every skill.
- Keep installation commands, update commands, tool names, and skill execution
  flows unchanged.

## Compatibility

The skills will not say that they are manual-only and will not forbid scheduled
execution. This avoids conflicting instructions if Hermes gains supported cron
integration later.

## Tests

- Continue verifying all five install and update commands.
- Verify skill metadata contains no `cron` tag.
- Verify the public package contains no current `hermes cron` commands.

## Out Of Scope

- Changing fetch or dashboard write behavior.
- Removing existing jobs from a Hermes installation.
- Implementing future Hermes cron support.
