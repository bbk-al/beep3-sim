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

setDev()

# Energy components
ea <- 3.1
eb <- 9.3
ec <- 9.3
P <- -0.04
MPL <- 0.008
EB <- function(r, M, N, L) {
	(-1)*pi*eb*ec*P*r
}
EB2 <- function(r, M, N, L12) {
	p1 <- (-1)*P*((r-L12)^3/(3*ea*ea) - r + L12)
	p2 <- 2*M*(r*r/2 - 2*L12*r + 3*L12*L12/2 + L12*L12*log(r/L12)) / (3*ea*ea)
	(-1)*pi*eb*ec*(p1+p2)
}
# LN1 -> L_(N-1)
ENL <- function(r, M, N, LN1) {
	p1 <- (r*r/2 - 2*LN*r + 3*LN*LN/2)/(ea*ea)
	p2 <- (LN*LN/(ea*ea) - 1)*log(r/LN)
	pi*eb*ec*M*(p1+p2)*(N-1)/N
}
ENM <- function(r, M, N, LN1) {
	(-1)*(N-1)*pi*eb*ec*M*log(r/(LN1+ea))/N
}
ENH <- function(r, M, N, LN) {
	NN1 <- N*(N+1)
	p1 <- (r*r/2 - 2*LN*r + 3*LN*LN/2)/(NN1*ea*ea)
	p2 <- (LN*LN/(NN1*ea*ea) + (N-1)/N)*log(r/LN)
	(-1)*pi*eb*ec*M*(p1+p2)
}


png("hen.png")
xlab <- expression(paste("r (", ring(A), ")", sep=""))
ylab <- expression(paste("Energy (kJ mo", l^-1, ")", sep=""))
Lk <- list(
		c(1.4, 1.4), c(2.1, 1.4), c(2.1, 4.2),
		c(1.4, 2.1), c(2.1, 2.1), c(2.8, 2.1),
		c(1.4, 2.8), c(2.1, 2.8), c(2.1, 3.5))
colours <- hsv(seq(0.0,1.0,length.out=length(Lk)),1,1)
rlb <- 0.0
rub <- 20.0
r <- seq(rlb,rub,0.01)
plot(0,0,ty="n",xlim=c(rlb,rub),ylim=c(0,125),xlab=xlab,ylab=ylab)
mtext("ENL")
for (n in 1:length(Lk)) {
	E <- rep(0.0,length(r))
	k <- Lk[[n]][2]
	L <- k+Lk[[n]][1]*(1:5)
if (TRUE) {
	limit <- c(min(r), c(L[2:5],L[2:5]+ea)[order(c(seq_along(L[2:5]), seq_along(L[2:5]+ea)))])
	nterms <- length(limit)-1
	fn <- c("EB", "EB2", rep(c("ENM", "ENH"),nterms/2))

	for (i in 1:nterms) {
		range <- (r>limit[i] & r<limit[i+1])
		if (length(range) > 0) {
			M <- MPL*L[i/2]
			E[range] <- E[range] + do.call(fn[i], list(r[range], M, floor((i+3)/2), L[(i+2)/2]))
			mr <- (1:length(r))[range]
			if (length(mr) > 0) {
				m <- max(mr) + 1
				if (m <= length(r)) {
					s <- seq(m, length(r))
					E[s] <- E[s] + do.call(fn[i], list(limit[i+1], M, floor((i+3)/2), L[(i+2)/2]))
				}
			}
		}
	}
	lines(r, E, col=colours[n])
} else{
	range <- (r<=L[2])
	if (length(range) > 0) {
		E[range] <- E[range] + EB(r[range], 1, 2, 3)
		mr <- (1:length(r))[range]
		if (length(mr) > 0) {
			m <- max(mr) + 1
			if (m <= length(r)) {
				s <- seq(m, length(r))
				E[s] <- E[s] + EB(L[2], 1, 2, 3)
			}
		}
	}

	range <- (r>L[2] & r<=(L[2]+ea))
	if (length(range) > 0) {
		M <- MPL*L[2]
		E[range] <- E[range] + EB2(r[range], M, 2, L[2])
		mr <- (1:length(r))[range]
		if (length(mr) > 0) {
			m <- max(mr) + 1
			if (m <= length(r)) {
				s <- seq(m, length(r))
				E[s] <- E[s] + EB2(L[2]+ea, M, 2, L[2])
			}
		}
	}

	range <- (r>(L[2]+ea) & r<=L[3])
	if (length(range) > 0) {
		M <- MPL*L[3]
		E[range] <- E[range] + ENM(r[range], M, 3, L[2])
		mr <- (1:length(r))[range]
		if (length(mr) > 0) {
			m <- max(mr) + 1
			if (m <= length(r)) {
				s <- seq(m, length(r))
				E[s] <- E[s] + ENM(L[3], M, 3, L[2])
			}
		}
	}

	range <- (r>L[3] & r<=(L[3]+ea))
	if (length(range) > 0) {
		M <- MPL*L[3]
		E[range] <- E[range] + ENH(r[range], M, 3, L[3])
		mr <- (1:length(r))[range]
		if (length(mr) > 0) {
			m <- max(mr) + 1
			if (m <= length(r)) {
				s <- seq(m, length(r))
				E[s] <- E[s] + ENH(L[3]+ea, M, 3, L[3])
			}
		}
	}

	range <- (r>(L[3]+ea) & r<=L[4])
	if (length(range) > 0) {
		M <- MPL*L[4]
		E[range] <- E[range] + ENM(r[range], M, 4, L[3])
		mr <- (1:length(r))[range]
		if (length(mr) > 0) {
			m <- max(mr) + 1
			if (m <= length(r)) {
				s <- seq(m, length(r))
				E[s] <- E[s] + ENM(L[4], M, 4, L[3])
			}
		}
	}
	lines(r, E, col=colours[n])
}
}
legend('topleft', 'groups', ncol=2, bty ="n",
		Lk, col=colours, lty=1)

pause("exit")


