This is a very simple script to be used with `mapillary-tools`,
to clean up sequences made with GoPro Hero 9+ timelapse JPGs
to be uploaded to Mapillary.

Things from GoPro images that should be fixed before upload:
* Datetime will be recorded as local time but Mapillary accepts UTC.
* Sequence cut and distance-based duplication check.

Only tested with my GoPro Hero 10.

### Instruction

Install Mapillary tools and this with `pipx`:
```bash
pipx install git+https://github.com/mapillary/mapillary_tools
pipx install git+https://github.com/littlebtc/mapillary-cleanup
```

Assume you copy all the `xxxGOPRO` folders from `DCIM` in the Micro SD card
to a folder named `imgs`. Then running the following command to process and upload them:

```bash
mapillary_tools process imgs --interpolate_directions
mapillary_cleanup -h "-8" -m 1 imgs
mapillary_tools upload imgs
```

Args:
* `-h`: hours to be added or substracted (default: 0).
* `-m`: distance in meters to be considered as duplicate (default: 0, which will not apply checks).
* `-n`: Images to be included in the sequences. (default: 150)
