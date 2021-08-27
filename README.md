## Personal Scripts

### gettext-rs

```shell
gettext_rs.py [-h] [-s SRC_DIR] [-b BUILD_DIR]
```

Hack to generate pot files for rust files with gettext macros. For some reason,
normal ninja pot generator doesn't detect rust gettext macros (i.e. gettext!) 
even when added as a keyword. This temporarily removes the `!`, generate the pot
file, and restore the previous state.

### make-release

```shell
make_release.py [-h] [-p PROJECT_DIR] [-n NEW_VERSION]
```

Replaces the version on meson.build and Cargo.toml to the version provided. It
skips them when the files are not found. It also opens gedit to ask for release
notes which will be written automatically to the metainfo file. It is also
skipped when either the file is not found or cancelled. Optionally, the diff
between the last tagged version to main is shown in the browser. After that, the
changes are committed and pushed when permitted. The release notes is
automatically copied to the clipboard or print if copying failed. Finally, it is
asked whether it is preferred to open browser to create a new release.
