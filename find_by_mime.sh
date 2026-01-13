# Save this as find_by_mime.sh
#!/bin/bash
MIME_TYPE="$1"
DIRECTORY="${2:-.}"

find "$DIRECTORY" -type f -exec sh -c '
    mime=$(file --mime-type -b "$1")
    [ "$mime" = "'"$MIME_TYPE"'" ] && echo "$1"
' _ {} \;