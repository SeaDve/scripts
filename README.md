## Personal Scripts

### gettext-rs

```shell
python gettext-rs.py [-h] project_name src_dir build_dir
```

Hack to generate pot files for rust files with gettext macros. For some reason,
normal ninja pot generator doesn't detect rust gettext macros (i.e. gettext!) 
even when added as a keyword. This temporarily removes the `!`, generate the pot
file, and restore the previous state.

### release-notes

```shell
python release-notes.py [-h] appstream_file
```

Generate a release note based on the latest release in the appstream file.
