#!/usr/bin/env Rscript
# Read in salt.dat and plot points
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
p <- arg_parser("Plot salt effects")
p <- add_argument(p,
        c("--file", "--start", "--increment", "--xlabel"),
        help = c("salt data file", "starting separation", "increment",
				 "uncapitalised x-axis label"),
		default=list(file="salt", start=25, increment=-0.5,
					 xlabel="separation"), 
        flag = c(FALSE, FALSE, FALSE, FALSE))
p <- add_argument(p,
		c("--png"),
		help=c("generate PNG file"),
		flag=c(TRUE))
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

# Prep locations
loc <- argv$start-argv$increment
ks <- df$kappa[1]
n <- 1
while (n <= length(df$mi)) {
	if (df$kappa[n] != ks) {
		ks <- df$kappa[n]
		loc <- argv$start-argv$increment
	}
	if (df$mi[n] == 0) loc <- loc+argv$increment
	df$location[n] <- loc
	n <- n+1
}
print(c(min(df$location),max(df$location)))
x <- seq(from=min(df$location),to=max(df$location),
		 length.out=length(unique(df$location)))

# Prep salt-dielectric
df$sd <- paste(expression(kappa),"=",df$kappa,", dielectric=",df$dielectric,sep="")
sdset <- unique(df$sd)

# Prep energies as new data frame
nr <- length(sdset)*length(x)
de <- data.frame(e=numeric(nr), sd=character(nr), location=numeric(nr),
				stringsAsFactors=FALSE)
n <- 1
for (sd in sdset) {
	for (xv in x) {
		de$sd[n] <- sd
		de$location[n] <- xv
		de$e[n] <- sum(df$e[df$sd == sd & df$location == xv])
		n <- n+1
	}
	de$e[de$sd==sd] <- de$e[de$sd==sd]-de$e[de$sd==sd&de$location==max(de$location)]
}

# Main plot
xlab <- capitalize(argv$xlabel)
ylim <- c(min(de$e),max(de$e))
ylim[2] <- ylim[2]*1.2-ylim[1]*0.2
colset <- hsv(seq(from=0.0,to=0.8,length.out=length(sdset)),1,1)
plot(0,0,ty="n",xlim=c(min(x),max(x)),ylim=ylim,
	xlab=xlab,ylab="Energy (kJ/mol)")
n <- 1
for (sd in sdset) {
	lines(x,de$e[de$sd==sd],col=colset[n])
	n <- n+1
}
legend('topleft', 'groups', ncol=2, bty ="n", sdset, lty=1, col=colset)

if (!argv$png) pause("exit")

