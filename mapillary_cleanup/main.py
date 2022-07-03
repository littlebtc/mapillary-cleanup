from datetime import datetime, timedelta
from json import load, dump
from pathlib import Path
from typing import IO, Any, Optional
from uuid import uuid4

from click import argument, command, option, Path as ClickPath
from geopy.distance import geodesic


FORMAT = "%Y_%m_%d_%H_%M_%S_%f"


@command()
@option("-h", default=0, type=float, help="Hours to be added / substracted")
@option("-m", default=0, type=float, help="Meters to be considered as duplicate point")
@option("-n", default=150, type=int, help="Images to split a sequence")
@argument(
    "input",
    type=ClickPath(exists=True, file_okay=False, writable=False, resolve_path=True),
)
def process(h: float, m: float, n: int, input: IO):
    got = 0
    skipped = 0
    prev_point: Optional[tuple[float, float]] = None
    json_path: Path = Path(input) / "mapillary_image_description.json"
    errors: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seq_id = str(uuid4())
    with json_path.open("r+") as fd:
        orig = load(fd)
        for img in orig:
            if "error" in img:
                errors.append(img)
                continue
            point: tuple[float, float] = img["MAPLatitude"], img["MAPLongitude"]
            if got == n:
                seq_id = str(uuid4())
                got = 1
            else:
                got += 1
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

            if h != 0:
                time = datetime.strptime(img["MAPCaptureTime"], FORMAT)
                img["MAPCaptureTime"] = datetime.strftime(
                    time + timedelta(hours=h), FORMAT
                )[:-3]
            
            img["MAPSequenceUUID"] = seq_id
            results.append(img)

        fd.seek(0)
        dump(errors + results, fd, indent=4)
        fd.truncate()

    print(f"{skipped} images are skipped")
