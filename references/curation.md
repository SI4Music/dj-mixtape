# Crate curation

Select recordings matching the user's language/genre, not merely search titles. Prefer official artist or label uploads. Keep title, channel, URL, upload date, delivery format and SHA-256. Search is discovery evidence; selected download metadata confirms uploader identity.

Catalog JSON: `title`, `tracks`, with each track's stable `id`, `artist`, `title`, `url`, `section`, relative `energy` (1–5) and optional `source_note`. Source duration must exceed the planned excerpt; selected music must exceed target duration after cuts/overlaps. Keep alternatives for unavailable or unsuitable recordings.

Do not silently use teasers, concert footage, sped-up edits, remixes or existing nonstop compilations when individual originals are requested. Music videos can contain dialogue/end credits; account for those in preparation. Use a bounded retry and select an alternative when availability is unchanged.
