#!/usr/bin/env Rscript
# Display memory usage and timing data
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

# Process arguments
suppressPackageStartupMessages({
require('Hmisc')
require('argparser')
})
p <- arg_parser("Plot interaction areas data")
p <- add_argument(p,
        c("--file", "--maxa"),
        help = c("areas data file", "maximum area"),
		default=list(file="areas.dat", maxa=0),
        flag = c(FALSE,FALSE))
p <- add_argument(p,
		c("--png", "--log"),
		help=c("generate PNG file", "use a log scale for area"),
		flag=c(TRUE, TRUE))
argv <- parse_args(p)

# Read the data
df <- read.table(argv$file, comment.char="")

# Main plot
if (argv$png) {
	pngfile <- sub("\\.[a-z][a-z][a-z]$", ".png", argv$file)
	if (length(pngfile) > 0) {
		png(pngfile)
	} else {
		cat("Failed to interpret filename\n")
		exit()
	}
} else {
	setDev()
}

df <- read.table(argv$file)
print(c(max(df$area),df$mi[which.max(df$area)]))
colset <- hsv(c(0,0.1,seq(from=0.2,to=0.8,length.out=max(df$mi)-1)),1,1)
if (argv$maxa == 0) argv$maxa = max(df$area)
lg <- ""
if (argv$log) {
	df$area <- df$area+1
	lg <- "y"
}
plot(df$area, log=lg, col=colset[1+df$mi], ylim=c(min(df$area),argv$maxa),
	ylab=expression(paste("Change in Hydrophobic Interaction Area (", ring(A), ")", sep="")))
# plot(density(df$area[df$mi>1]),xlab="Area",main="Density of crowder HE        interaction area")

if (!argv$png) pause("exit")
