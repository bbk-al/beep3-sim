#!/usr/bin/env Rscript
# Display iteration convergence data
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
p <- arg_parser("Plot iteration convergence data.  Note: if a directory is specified, if energies.dat exists, error margins are plotted instead of raw convergence levels.")
p <- add_argument(p,
        c("--file", "--maxi", "--ecomp", "--xlabel", "--scale"),
        help = c("iter data file", "maximum GMRES iteration count",
				"error axis multiplier", "x-axis label", "x value multiplier"),
		default=list(file=".", maxi=0, elim=1, xlabel="Iteration", scale=1),
        flag = c(FALSE, FALSE, FALSE, FALSE, FALSE))
p <- add_argument(p,
		c("--png"),
		help=c("generate PNG file"),
		flag=c(TRUE))
argv <- parse_args(p)

# Convert the file name
ifile = argv$file
efile = ""
n <- nchar(argv$file)
if (n > 3 && substr(argv$file,(n-3),n) != ".dat") {
	ifile = paste(argv$file, "/iter.dat", sep="")
	efile = paste(argv$file, "/energies.dat", sep="")
}

# Read the data
di <- read.table(ifile, comment.char="")
e <- vector()
if (efile != "") {
	de <- read.table(efile, comment.char="")
	if ("it" %in% colnames(de)) {
		e <- sapply(seq(min(de$it),max(de$it)),
					FUN=function(x) sum(de$e[de$it==x]))
		if (length(e) != length(di$convergence)) {
			cat("Mismatched data lengths - reverting to convergence plot\n")
			efile = ""
		}
	} else {
		efile = ""
	}
}

# Main plot
if (argv$png) {
	pngfile <- paste(argv$file, "/iter.png", sep="")
	if (efile == "") {
		pngfile <- sub("\\.[a-z][a-z][a-z]$", ".png", argv$file)
	}
	if (length(pngfile) > 0) {
		png(pngfile)
	} else {
		cat("Failed to interpret filename\n")
		exit()
	}
} else {
	setDev()
}

# Combined plot
x <- seq(0, length(di$count)-1)
x <- x*argv$scale
par(mar = c(5, 4, 4, 4) + 0.3)  # Leave space for convergence axis
maxi <- max(di$count)
if (argv$maxi != 0) maxi <- argv$maxi
plot(x,di$count,ylim=c(0,maxi),ty="l",xlab=capitalize(argv$xlabel),ylab="GMRES Iteration count")
if (efile == "") {
	z <- abs(di$convergence)
	mt <- "Convergence"
} else {
	z <- abs(e/di$convergence)
	mt <- expression(paste("Error (kJ ", mol^{-1}, ")", sep=""))
}
elim <- range(c(z,z*argv$ecomp),na.rm=TRUE)
par(new=TRUE)
plot(x,z,ty="l",log="y",ylim=elim,col="blue",axes = FALSE,bty = "n",
	 xlab = "",ylab = "")
print(elim)
axis(side=4,col="blue",col.axis="blue",at=axisTicks(log10(elim),log=TRUE,n=n))
mtext(mt, col="blue", side=4, line=3)

if (!argv$png) pause("exit")

