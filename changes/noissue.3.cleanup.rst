Dev: Relaxed the conditions when safety issues are tolerated:
Issues in development dependencies are now tolerated in normal and scheduled
test workflow runs (but not in local make runs and release test workflow runs).
Issues in installation dependencies are now tolerated in normal test workflow
runs (but not in local make runs and scheduled/release test workflow runs).
