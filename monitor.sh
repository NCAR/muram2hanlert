export ITERDIR="jobs/coolvel/iter_16000"
watch -n 300 sh -c 'date; echo Prepared: $(find $ITERDIR -mindepth 2 -maxdepth 2 | wc -l); echo All Queue: $(qstat | wc -l); echo Queued: $(qstat -u egeland -S Q | wc -l); echo Running: $(qstat -u egeland -S R | wc -l); echo Complete: $(find $ITERDIR -type f -name Stokes_1_1 | wc -l);'

# they changed this
# echo Failed: $(qhist -d 1 -f -u egeland -w | wc -l)
