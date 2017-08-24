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
p <- arg_parser("Plot density or histogram of separation data from results.py")
p <- add_argument(p,
        c("--file", "--breaks"),
        help = c("separations data file", "number of histogram breaks"),
		default=list(file=".", breaks="Sturges"),
        flag = c(FALSE, FALSE))
p <- add_argument(p,
		c("--png", "--hist", "--subject"),
		help=c("generate PNG file", "plot histogram", "data is crowder-subject"),
		flag=c(TRUE,TRUE,TRUE))
argv <- parse_args(p)
if (!is.na(as.integer(argv$breaks))) argv$breaks = as.integer(argv$breaks)

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

# Combined plot
print(c(mean(df$initial), mean(df$final)))
if (argv$hist) {
	merge <- hist(range(c(df$initial,df$final)),breaks=argv$breaks)
	xyi <- hist(df$initial, breaks=merge$breaks)
	xyf <- hist(df$final, breaks=merge$breaks)
	yr <- c(min(c(xyi$counts,xyf$counts)),max(c(xyi$counts,xyf$counts)))
print(yr)
	mt <- "Frequency"
	al <- 0.2
	nc <- 3
} else {
	xyi <- density(df$initial)
	xyf <- density(df$final)
	yr <- c(min(c(xyi$y,xyf$y)),max(c(xyi$y,xyf$y)))
	mt <- "Density"
	al <- 1.0
	nc <- 2
}
ci <- alpha("blue",al)
cf <- alpha("red",al)
# This is a bit nasty - is there an easier way to combine alpha colours?
ccrgb <- (col2rgb(ci) + col2rgb(cf))/510
cc <- alpha(rgb(ccrgb[1], ccrgb[2], ccrgb[3], 0.32))
if (argv$subject) {
	partner <- "subject"
} else {
	partner <- "crowder"
}
plot(xyi,ylim=yr,col=ci,xlab=expression(paste("Separation (",ring(A),")",sep="")),main=paste(mt," of crowder-",partner," separations", sep=""))
if (argv$hist) {
	plot(xyf,col=cf,add=T)
} else {
	lines(xyf,col=cf)
}
legend('topleft', 'groups', ncol=2, bty ="n",
		c("initial", "final", "overlap")[1:nc], fill=c(ci, cf, cc)[1:nc])

if (!argv$png) pause("exit")

