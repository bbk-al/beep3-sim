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
MPL <- 0.004
q <- 0.5
EB <- function(r, M, N, L, LM, L1M) {
	(-1)*pi*eb*ec*P*r
}
EB2 <- function(r, M, N, L12, L2M, L3M) {
	#p1 <- (-1)*P*((r-L12)^3/(3*ea*ea) - r + L12)
	#p2 <- 2*M*(r*r/2 - 2*L12*r + 3*L12*L12/2 + L12*L12*log(r/L12)) / (ea*ea)
	p1 <- (-1)*(P+M)*((r-L12)^3/(3*ea*ea)) - P*(L12-r)
	p2 <- M*L2M*(r*r/2 - 2*L12*r + 3*L12*L12/2 + L12*L12*log(r/L12)) / (ea*ea)
	(-1)*pi*eb*ec*(p1+p2)
}
# LN1 -> L_(N-1)
# Unused...
ENL <- function(r, M, N, LN1, LN1M, LNM) {
	p1 <- (r*r/2 - 2*LN*r + 3*LN*LN/2)/(ea*ea)
	p2 <- ((LN*LN/(ea*ea) - 1)*log(r/LN))*(N-1)/N
	pi*eb*ec*M*(p1+p2)*(N-1)/N
}
ENM <- function(r, M, N, LN1, LN1M, LNM) {
	(-1)*pi*eb*ec*M*(LN1M*log(r/(LN1+ea) - r + LN1+ea))*(N-1)/N
}
# LN1 -> L_(N+1)
ENH <- function(r, M, N, LN, LNM, LN1M) {
	NN1 <- N*LN1M/(N+1) - (N-1)*LNM/N
	p1 <- (r*r/2 - 2*LN*r + 3*LN*LN/2)*NN1/(ea*ea)
	p2 <- (LN*LN*NN1/(ea*ea) + (N-1)*LNM/N)*log(r/LN) + (LN-r)*(N-1)/N
	p3 <- ((r - LN)^3)/(3*ea*ea*N*(N+1))
	(-1)*pi*eb*ec*M*(p1+p2+p3)
}


#png("hen.png")
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
			N <- floor((i+3)/2)
			LN <- L[(i+2)/2]
			LNQ <- q*L[(i+1)/2]+(1-q)*LN
			LN1Q <- q*LN+(1-q)*L[(i+3)/2]
			E[range] <- E[range] +
						 do.call(fn[i], list(r[range], M, N, LN, LNQ, LN1Q))
			mr <- (1:length(r))[range]
			if (length(mr) > 0) {
				m <- max(mr) + 1
				if (m <= length(r)) {
					s <- seq(m, length(r))
					E[s] <- E[s] +
							 do.call(fn[i], list(limit[i+1], M,N,LN,LNQ,LN1Q))
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


