#!/usr/bin/env Rscript # Read in results.txt and plot points
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


library(plot3D)
# Read the data
df <- read.table("scenario-1-0.txt")
print(str(df))

# Process colours
df$c[df$c > 1] <- 2
df$c <- 1+df$c

# Estimate sizes
f <- max(max(df$x)-min(df$x),max(df$y)-min(df$y),max(df$z)-min(df$z)) /
		(60*max(df$s))
df$s <- df$s * f

# Plot!
do_plot <- FALSE
if (!interactive()) {
	do_plot <- TRUE
	png(file="scenario-3D-r.png")
}
scatter3D(x=df$x, y=df$y, z=df$z, colvar=df$c, pch='o', cex=df$s,
		 xaxp=c(min(df$x),max(df$x),10), ticktype="detailed",
		 xlab="x", ylab="y", zlab="z", plot=do_plot)
if (interactive()) {
	plotrgl()
	par3d(windowRect=c(0, 45, 780, 780))
}

