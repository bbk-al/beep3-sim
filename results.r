#!/usr/bin/env Rscript
# Read in results.txt and plot points
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


library(plot3Drgl)
# Marker, line and colour mapping
pymList <- c('o', '^', 'D', '*')		   # If results.py gives marker styles
pchList <- list(16, 17, 18, "*")
pylList <- c('solid', 'dotted', 'dashed')  # If results.py gives line types
ltyList <- list(3, 1, 2, 3)  # Map '*' to solid
pycList <- c('r', 'y', 'g', 'c', 'b', 'm', 'k')
colList <- c("red", "yellow", "green", "lightblue", "blue", "magenta", "black")

# Read the data
df <- read.table("results.txt")

# Plot!
do_plot <- FALSE
if (!interactive()) {
	do_plot <- TRUE
	png(file="run2-3DE-r.png")
}
arrows3D(x0=df$x, y0=df$y, z0=df$z,
		 x1=(df$x+df$u), y1=(df$y+df$v), z1=(df$z+df$w),
		 colvar=sapply(df$colour, function(x) which(pycList==x)),
		 pch=sapply(df$marker, function(x) ltyList[[which(pymList==x)]]),
		 xlab="x", ylab="y", zlab="z", col=colList, ticktype = "detailed",
		 plot=do_plot)
if (interactive()) {
	plotrgl()
	par3d(windowRect=c(0, 45, 780, 780))
}

