####################
particle_properties
####################


.. toctree::
	:maxdepth: 1

	AgeDecay.rst
	CustomParticleProperty.rst
	DistanceTravelled.rst
	FieldParticleProperty.rst
	FractionalWaterDepth.rst
	InsidePolygonsNonOverlapping2D.rst
	ManuallyUpdatedParticleProperty.rst
	ParticleLoad.rst
	ParticleParameterFromNormalDistribution.rst
	RouseNumber.rst
	TotalWaterDepth.rst
	VectorMagnitude2D.rst
	WaterSpeed.rst
	_BaseParticleProperty.rst

**Role:** Particle properties hold data at current time step for each particle, accessed using their ``"name"`` parameter. Particle properties  many be 
 * core properties set internally (eg particle location x )
 * derive from hindcast fields, 
 * be calculated from other particle properties by user added class.

