Simple script to generate pot file.

## Why?

For some reason, normal ninja pot generator doesn't detect
rust gettext macros (i.e. `gettext!`) even when added as a
keyword. So, I created this script to automatically remove 
the `!`, generate the pot file, then restore the state.

This script needs some improvement such as improving error
handling and removing the `shell=True` thing.
