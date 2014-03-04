# unlock

Unlock your Northeastern University, on campus, NFC enabled, dorm door via the
command line.

## configuration

`unlock.py` needs to authenticate via your myNEU credentials, and looks for
`~/.unlock.json` which looks something like:

```
{
    "USER": "smith.j",
    "PASS": "s3cure"
}
```

The first time you run `unlock.py`, it'll generate it for you, if you want.

## usage

If run with no arguments, it'll unlock the main door to your apartment,
essentially accomplishing the same thing as you putting your ID card next to
the door lock. To completely unlock the door, you'll need to enter your PIN.

If you live in IV or another place where you only have 1 door, it'll unlock 
that. As you might expect, the -r flag then does nothing.

```
$ ./unlock.py -h
usage: unlock.py [-h] [-r] [-v]

Unlock your Northeastern University on campus, NFC enabled, dorm door via the
command line.

optional arguments:
  -h, --help     show this help message and exit
  -r, --room     unlock your actual room door instead of your apartment's door
  -v, --verbose  display detailed info
```
