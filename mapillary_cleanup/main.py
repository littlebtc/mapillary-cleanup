from datetime import datetime, timedelta
from json import load, dump
from pathlib import Path
from typing import IO, Any, Optional
from uuid import uuid4
from zoneinfo import ZoneInfo

from click import argument, command, option, Path as ClickPath
from geopy.distance import geodesic


FORMAT = "%Y_%m_%d_%H_%M_%S_%f"


@command()
@option(
    "-z",
    default="UTC",
    type=str,
    help="Time zone recognized by tzinfo, used to convert timestamp to UTC",
)
@option("-m", default=0, type=float, help="Meters to be considered as duplicate point")
@option(
    "-n",
    default=200,
    type=int,
    help="Maximum images (including duplicates) in a sequence",
)
@option("-s", default=30, type=int, help="Seconds between images to split sequences")
@argument(
    "input",
    type=ClickPath(exists=True, file_okay=False, writable=False, resolve_path=True),
)
def process(z: str, m: float, n: int, s: int, input: IO):
    got = 0
    skipped = 0
    prev_point: Optional[tuple[float, float]] = None
    prev_time: Optional[datetime] = None
    json_path: Path = Path(input) / "mapillary_image_description.json"
    errors: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seq_id = str(uuid4())

    zone = ZoneInfo(z)
    with json_path.open("r+") as fd:
        orig = load(fd)
        for img in orig:    
            if "error" in img:
                errors.append(img)
                continue
            time = datetime.strptime(img["MAPCaptureTime"], FORMAT).replace(tzinfo=zone)
            point: tuple[float, float] = img["MAPLatitude"], img["MAPLongitude"]
            if got == n or (
                prev_time is not None and time - prev_time >= timedelta(seconds=s)
            ):
                seq_id = str(uuid4())
                got = 1
            else:
                got += 1
            prev_time = time
            if m > 0:
                dist = (
                    geodesic(prev_point, point).m
                    if prev_point is not None
                    else float("inf")
                )
                prev_point = point
                if dist < m:
                    errors.append(
                        {
                            "error": {
                                "type": "MapillaryDuplicationError",
                                "message": "Removed with mapillary-cleanup",
                            },
                            "filename": img["filename"],
                        }
                    )
                    skipped += 1
                    continue

            img["MAPCaptureTime"] = datetime.strftime(
                time.astimezone(ZoneInfo("UTC")), FORMAT
            )[:-3]

            img["MAPSequenceUUID"] = seq_id
            results.append(img)

        fd.seek(0)
        dump(errors + results, fd, indent=4)
        fd.truncate()

    print(f"{skipped} images are skipped")
