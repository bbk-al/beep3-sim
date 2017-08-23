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

# Extra modelling...
bestFit <- function(x,y,prediction,png) {
	# Take only the lower values to exclude noise
	my <- vector()
	mx <- vector()
	p <- 1
	for (n in seq(1,length(y)-1)) {
		if (min(y[(n+1):length(y)]) > y[n]) {
			my[p] <- y[n]
			mx[p] <- x[n]
			p <- p+1
		}
	}

	# Try a well-known series of likely models
	m <- list()
	m[[1]] <- lm(my ~ mx)
	m[[2]] <- lm(my ~ mx + I(mx^2)) # + I(x^3))
	m[[3]] <- lm(my ~ mx + I(mx^2) + I(mx^3))
	m[[4]] <- lm(my ~ mx + I(mx^2) + I(mx^3) + I(mx^4))
	m[[5]] <- lm(my ~ mx*log(mx+0.1))
	#z <- mx*log(mx+0.1)
	#m[[5]] <- lm(my ~ z)
	bf <- which.max(sapply(seq(1,length(m)),
					FUN=function(n) summary(m[[n]])$fstatistic[1]))
	for (sm in m) print(c(summary(sm)$r.squared,summary(sm)$fstatistic))


	if (prediction) {
		par(mfrow=c(2,2))
		plot(predict(m[[1]]),my,main="m1")
		plot(predict(m[[2]]),my,main="m2")
		plot(predict(m[[3]]),my,main="m3")
		plot(predict(m[[5]]),my,main="ml")
		if (!png) pause("continue")
	}

	return(m[[bf]])
}

# Process arguments
suppressPackageStartupMessages({
require('Hmisc')
require('argparser')
})
p <- arg_parser("Plot memory and time data")
p <- add_argument(p,
        c("--file", "--maxm", "--maxt", "--xlabel", "--scale"),
        help = c("memtime data file", "maximum memory", "maximum time",
				"x-axis label", "x value multiplier"),
		default=list(file="memtime.dat", maxm=0, maxt=0,
					xlabel="Iteration", scale=1),
        flag = c(FALSE, FALSE, FALSE, FALSE, FALSE))
p <- add_argument(p,
		c("--png", "--model"),
		help=c("generate PNG file", "attempt a best fit model"),
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

par(mfrow=c(1,2))

# Memory plot
mmin <- min(df$memory)
mmax <- max(df$memory)
print(c(mmin,mmax))
if (argv$maxm != 0) mmax <- argv$maxm
x <- seq(0, length(df$memory)-1)
x <- x*argv$scale
plot(x,df$memory,ylim=c(0,mmax),ty="l",
	xlab=capitalize(argv$xlabel),ylab="Memory (MB)")
if (argv$model) {
	mm <- bestFit(x,df$memory,FALSE,FALSE)
	lines(mm$model$mx,mm$fitted.values,col="blue")
}

# Time plot
t <- tail(df$time,-1)-head(df$time,-1)
tmin <- min(t)
tmax <- max(t)
print(c(tmin,tmax))
if (argv$maxt != 0) tmax <- argv$maxt
x <- seq(0, length(t)-1)
x <- x*argv$scale
plot(x,t,ylim=c(0,tmax),ty="l",
	xlab=capitalize(argv$xlabel),ylab="Time to complete (s)")
if (argv$model) {
	mt <- bestFit(x,t, FALSE, FALSE)
	lines(mt$model$mx,mt$fitted.values,col="blue")
}

if (!argv$png) pause("exit")
