## Personal Scripts

### gettext-rs

```shell
python3 gettext-rs.py [-h] project_name src_dir build_dir
```

Hack to generate pot files for rust files with gettext macros. For some reason,
normal ninja pot generator doesn't detect rust gettext macros (i.e. gettext!) 
even when added as a keyword. This temporarily removes the `!`, generate the pot
file, and restore the previous state.

### make-release

```shell
python3 make-release.py [-h] project_dir version
```

Replaces the version on meson.build and Cargo.toml to the version provided. It
skips them when the files are not found. It also opens gedit to ask for release
notes which will be written automatically to the metainfo file. It is also 
skipped when either the file is not found or cancelled. Finally, the changes are
committed and pushed when permitted. The release notes is automatically copied
to the clipboard or print if copying failed.
