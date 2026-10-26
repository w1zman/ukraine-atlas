"""Filter NASA FIRMS VIIRS active-fire CSVs (last 24 h) to the Ukraine area and write a compact fires.json."""
import csv, io, json, sys, urllib.request, datetime

SOURCES = [
    ("S-NPP", "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Europe_24h.csv"),
    ("NOAA-20", "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Europe_24h.csv"),
    ("NOAA-21", "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-21-viirs-c2/csv/J2_VIIRS_C2_Europe_24h.csv"),
]
LON0, LON1, LAT0, LAT1 = 21.5, 41.0, 43.8, 53.0
fires, used = [], []
for name, url in SOURCES:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ukraine-atlas"}), timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:
        print("skip", name, e, file=sys.stderr)
        continue
    n = 0
    for row in csv.DictReader(io.StringIO(text)):
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (KeyError, ValueError):
            continue
        if not (LON0 <= lon <= LON1 and LAT0 <= lat <= LAT1):
            continue
        if row.get("confidence", "n").lower().startswith("l"):
            continue
        t = row.get("acq_time", "0000").zfill(4)
        fires.append([round(lon, 4), round(lat, 4), round(float(row.get("frp") or 0), 1),
                      f"{row.get('acq_date')}T{t[:2]}:{t[2:]}Z", name, row.get("daynight", "")])
        n += 1
    used.append({"satellite": name, "count": n})
if not used:
    sys.exit("no FIRMS source reachable")
fires.sort(key=lambda f: f[3])
json.dump({"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "sources": used, "fires": fires},
          open(sys.argv[1], "w"), separators=(",", ":"))
print(len(fires), "fires", used)
