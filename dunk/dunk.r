#!/usr/bin/env rscript
setDev <- function() {
    if (capabilities()["X11"]) {
        X11()
    } else if (capabilities()["aqua"]) {
        quartz()
    } else {
        warning("Unable to determine device to use.  See Rplots.pdf")
    }
}

# For cat-paste convenience...
endl <- "\n"

# Use locator() to pause displays...
pause <- function(prompt) {
    cat(paste("Click on plot for",prompt,endl))
    p <- locator(1)
}

setDev()

df <- read.table("/d/mw6/u/la002/pjt/dunk/ache_fas/results-10.txt")
#df <- read.table("/d/mw6/u/la002/pjt/dunk/ache_fas/results-all")
count <- ncol(df)

df$sep <- seq(from=10.165,to=58.165,by=2)

cols=c("brown", "red", "orange", "yellow", "green", "lightblue", "blue", "purple", "magenta", "black")
for (n in seq(1,count,by=1)) {
	plot(x=df$sep,y=df[["V"+n]],xlab="Separation (A)",ylab="Energy (kJ/mol)",
		col=cols[n])
}

pause("exit")

