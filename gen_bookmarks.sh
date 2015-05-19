#!/bin/bash

bookmark_cnt=0
error_cnt=0;

print_header () {
cat <<- END
<!doctype html>
<html>
 <head>
  <title>bookmark backups $(date)</title>
  <link rel="stylesheet" type="text/css" href="/bookmark_archive.css">
 </head>
 <body>
  <header>
   <h1>Bookmark archive</h1>
   <p>backups of various bookmarks from various browsers and various times</p>
  </header>
  <section class="bmark_archive">

END
}

gen_list () {
for bfile in `ls bookmarks_[0-9]*_*_*.html`;
do

	bf_form=$(echo $bfile|cut -d '.' -f 1 | cut -b 11- |awk -F '_' '{printf("%2d %.2d 20%d\n",$1, $2,$3); }')

	bf_stat=$(/usr/bin/stat --format '%y %s' $bfile)

	echo '<A href="./'$bfile'">'$bf_form'</a><p class="blist">'$bf_stat'</p><br />'
	: $((bookmark_cnt=bookmark_cnt+1))
done
}

print_footer () {
cat <<- END
  </section>
  <footer class="bmark_list">
   <hr >
   <p> Site generated on $(date)</p>
  </footer>
 </body>
 </html>
END
}

dprint () {
	[ -x /usr/bin/tty >/dev/null 2>&1 ] && echo "=> $*" > /dev/fd/2
}

####
# main() 
#

bmarkdir="/home/fred/public_html"
if [ -d $bmarkdir ]; then
	cd $bmarkdir
else
	dprint "!> Cannot chdir(2) to $bmarkdir"
fi
dprint 'Generating a list' 

print_header;
gen_list;
print_footer

dprint "Done added $bookmark_cnt files" 
