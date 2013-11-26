yours.py
========

Ultra simple python http server for local file transferts.

Still a proof of concept, but the use case is when you are coding with friends, and you want to share some files.
But not everyone has signed for [ Dropbox, Google Docs, Github, whatever ], and for whatsoever reason isn't willing to do so. The same issue stands for [ ssh, ftp, windows_i_don't_know_what_kind_of_nfs, webdav... ].

Looks like a quick and dirty file-sharing python http server could save the day.

Implemented untested features :
==============================
* navigation through directories
* download of single files
* upload of multiple files
* simili version management (files already there are moved and renamed before writing the uploaded file)

Required features :
===================
* design
* security audit
* tests
* get params from cli
* new directory
* download multiple files / directories (automatic compression)
* windows compatibility



