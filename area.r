#!/usr/bin/env Rscript
# Read in area.dat and plot points
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
library('argparser')
p <- arg_parser("Plot energy by area")
p <- add_argument(p,
        c("--file"),
        help = c("area data file"),
		default=list(file="area.dat"),
        flag = c(FALSE))
p <- add_argument(p, "--png", help="generate PNG files", flag=TRUE)
argv <- parse_args(p)

# Read the data
df <- read.table(argv$file, comment.char="")

minx <- min(df$pct)
maxx <- max(df$pct)

# NB plot((df$pct-10)*0.023, df$solve, xlab=expression("Linear shift " + ring(A)), ylab=expression("kJ mol"^-1), type='l', lty=1)

# Plot!
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
plot(0,0,ty="n",xlim=c(minx,maxx),ylim=c(0,1.2),xlab="%",ylab="Value variation")
pdblist <- unique(df$pdbid)
colours=rainbow(length(pdblist))
mtext("Variation of energy and area with simplification")
n <- 0
tol=1e-4
v <- list(vector(), vector(), vector(), vector())
cn <- c("area", "f", "h")
if (exists("solve", where=df)) {
	cn <- c(cn, "solve")
}
cnseq <- 1:length(cn)
for (pdb in pdblist) {
	n <- n+1
	pct <- df$pct[df$pdbid == pdb]
	for (i in cnseq) {
		v[[i]] <- df[[cn[i]]][df$pdbid == pdb]
		v[[i]] <- (v[[i]]-min(v[[i]])) /
				(max(v[[i]])+abs(max(v[[i]]))*tol-min(v[[i]]))
		lines(pct, v[[i]], lty=i, col=colours[n])
	}
}
legend('topleft', 'groups', ncol=3, bty ="n", pdblist, col=colours, lty=1)
legend('topright', 'groups', ncol=2, bty ="n", cn, lty=cnseq)

if (!argv$png) pause("continue")

if (argv$png) {
	pngfile <- sub("\\.png$", "-ebya.png", pngfile)
	if (length(pngfile) > 0) {
		png(pngfile)
	} else {
		cat("Failed to interpret filename\n")
		exit()
	}
} else {
	setDev()
}
plot(0,0,ty="n",xlim=c(0,1),ylim=c(0,1.2),xlab="Area variation",ylab="h variation")
n <- 0
for (pdb in pdblist) {
	n <- n+1
	a <- df$area[df$pdbid == pdb]
	h <- df$h[df$pdbid == pdb]
	a <- (a-min(a))/(max(a)-min(a))
	h <- (h-min(h))/(max(h)-min(h))
	mtext("Variation of energy with area by simplification")
	lines(h, a, lty=1, col=rainbow(length(pdblist))[n])
}
legend('topleft', 'groups', ncol=3, bty ="n", pdblist, col=colours, lty=1)

if (!argv$png) pause("continue")
