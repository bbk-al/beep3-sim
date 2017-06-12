#!/usr/bin/env Rscript
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

drawPlot <- function() {
	df <- read.table("results-all")
	#df <- read.table("/d/mw6/u/la002/pjt/dunk/ache_fas/results-all")
	count <- ncol(df)
	#print(count)
	rc <- length(df$V1)
	select=1:rc #c(-1,-2)

	#mind <- sapply(seq(1,count,by=1),FUN=function(x) min(df[[paste("V",x,sep="")]][-1]))
	mind <- sapply(seq(1,count,by=1),FUN=function(x) df[[paste("V",x,sep="")]][rc])
	#print(mind)
	da <- sapply(seq(1,count,by=1),FUN=function(x) df[[paste("V",x,sep="")]][select]-mind[x])
	miny <- -15 #min(da)
	maxy <- 0 #max(da)
	#df$sep <- seq(from=10.165,to=58.165,by=2)
	#print(da)
	#print(maxy)
	if (count <= 10) {
		x <- seq(0.01,0.01*count,by=0.01)
	} else {
		x <- c(seq(0.01,0.1,by=0.01),seq(0.2,0.1*(count-9),by=0.1))
	}
	leg <- paste(x) #paste(seq(10,10*count,by=10))
	#print(leg)

	cols <- rainbow(count)
	#print(cols)
	#c("brown", "red", "orange", "yellow", "green", "lightblue", "blue",        "purple", "magenta", "black")
	for (n in c(10)) { #seq(1,count,by=1)) {
		plot(x=seq(from=10.165,to=58.165,by=2)[1:rc][select],y=da[,n],xlab="Separation (A)",
			ylab="Energy (kJ/mol)", col=cols[n],ty="l",ylim=c(miny,maxy))
		par(new=TRUE)
	}
	legend("topright",legend=leg,col=cols[1:count],lwd=3)
}

# Main program

setDev()

#par(mfrow=c(2,2))
for (f in c(4)) { #c("",1,3,4)) {
	rv <- system(paste("scp la002@ssh.cryst.bbk.ac.uk:/d/mw6/u/la002/pjt/dunk/",
				"ache_fas", f, "/results-all .", sep=""))
	if (rv == 0) drawPlot()
}

pause("exit")


