#!/usr/bin/env Rscript
# Read in energies.dat and plot points
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
p <- arg_parser("Plot energies breakdown")
p <- add_argument(p,
        c("--file", "--start", "--increment", "--yscale", "--xlabel"),
        help = c("energies data file", "starting separation", "increment",
				 "ymin,ymax", "uncapitalised x-axis label"),
		default=list(file="energies.dat", start=25, increment=-0.5,
					 yscale="", xlabel="separation"), 
        flag = c(FALSE, FALSE, FALSE, FALSE, FALSE))
p <- add_argument(p,
		c("--png", "--changes", "--nototal", "--totalonly"),
		help=c("generate PNG file", "plot change points only",
				"do not display total chart", "only display the total chart"),
		flag=c(TRUE, TRUE, TRUE, TRUE))
argv <- parse_args(p)

ymin <- Inf
ymax <- -Inf
if (argv$yscale != "") {
	y <- eval(parse(text=paste("c(", argv$yscale, ")", sep="")))
	ymin <- y[1]
	ymax <- y[2]
}

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
if (ymin == Inf) {
	n <- 0
	while (TRUE) {
		t <- df$t[df$mi == n]
		if (length(t) == 0) break;
		he <- df$he[df$mi == n]
		lj <- df$lj[df$mi == n]
		e <- df$e[df$mi == n]
	
		t <- t - min(e)
		e <- e - min(e)

		ymin <- min(ymin, min(t), min(e), min(he), min(lj))
		ymax <- max(ymax, max(t), max(e), max(he), max(lj))
		n <- n+1
	}
}

myplot <- function(changes, x, d, ty, c) {
	if (changes) {
		points(x, d, pch=ty, col=c)
	} else {
		lines(x, d, lty=ty, col=c)
	}
}


# Main plot
	
x <- seq(argv$start, by=argv$incr, length.out=length(df$t[df$mi == 0]))
xlab <- capitalize(argv$xlabel)
#xlab <- expression(paste("Linear shift +", ring(A), sep=""))
#colset <- rainbow(max(df$mi)+1)
colset <- hsv(c(0,0.1,seq(from=0.2,to=0.8,length.out=max(df$mi)-1)),1,1)
if (argv$changes) colset <- alpha(colset,0.5)
print(c(ymin,ymax))
if (argv$totalonly) {
	ct <- max(df$mi)+1
	y <- sapply(seq(1,length(x)),
				FUN=function(n) sum(df$t[((n-1)*ct+1):(n*ct)]))
	ymax <- max(y)
	ymin <- min(y)
	plot(x,y,ty="l",xlim=c(min(x),max(x)),ylim=c(ymin,ymax+0.1*(ymax-ymin)),
		xlab=xlab,ylab="Energy (kJ/mol)")
} else {
	plot(0,0,ty="n",xlim=c(min(x),max(x)),ylim=c(ymin,ymax+0.1*(ymax-ymin)),
		xlab=xlab,ylab="Energy (kJ/mol)")
}
n <- 0
if (argv$changes) {
	pty <- c(1, 16, 24, 15)
} else {
	pty <- c(1, 2, 3, 4)
}
while (!argv$totalonly) {
	t <- df$t[df$mi == n]
	if (length(t) == 0) break;
	he <- df$he[df$mi == n]
	lj <- df$lj[df$mi == n]
	e <- df$e[df$mi == n]
	
	t <- t - min(e)
	e <- e - min(e)

	if (argv$changes) {
		he[he == c(0,he)[1:length(he)]] <- NA
		lj[lj == c(0,lj)[1:length(lj)]] <- NA
		e[e == c(0,e)[1:length(e)]] <- NA
		t[t == c(0,t)[1:length(t)]] <- NA
	}

	n <- n+1
	
	mtext(paste("Variation of energy by", argv$xlabel, "by contribution"))
	if (!argv$nototal) myplot(argv$changes, x, t, pty[1], colset[n])
	myplot(argv$changes, x, he, pty[2], colset[n])
	myplot(argv$changes, x, lj, pty[3], colset[n])
	myplot(argv$changes, x, e, pty[4], colset[n])
}
if (!argv$totalonly) {
	n <- 4
	if (argv$nototal) n <- 3
	if (argv$changes) {
		legend('topleft', 'groups', ncol=n, bty ="n",
				c("HE", "LJ", "e", "total")[1:n], pch=pty[c(2,3,4,1)][1:n])
	} else {
		legend('topleft', 'groups', ncol=n, bty ="n",
				c("HE", "LJ", "e", "total")[1:n], lty=pty[c(2,3,4,1)][1:n])
	}
}

if (!argv$png) pause("continue")

# HE profile
if (argv$png) {
	pngfile <- sub("\\.png$", "-he.png", pngfile)
	if (length(pngfile) > 0) {
		png(pngfile)
	} else {
		cat("Failed to interpret filename\n")
		exit()
	}
} else {
	setDev()
}
d <- density(df$he)
plot(d, xlim=c(min(df$he),max(df$he)), xlab="Hydrophobic Effect Energy (kJ/mol)", ylab="Density",
main="Density plot of Hydrophobic Effect Energy")

if (!argv$png) pause("continue")
