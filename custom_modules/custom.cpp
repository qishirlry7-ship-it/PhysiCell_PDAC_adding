/*
###############################################################################
# If you use PhysiCell in your project, please cite PhysiCell and the version #
# number, such as below:                                                      #
#                                                                             #
# We implemented and solved the model using PhysiCell (Version x.y.z) [1].    #
#                                                                             #
# [1] A Ghaffarizadeh, R Heiland, SH Friedman, SM Mumenthaler, and P Macklin, #
#     PhysiCell: an Open Source Physics-Based Cell Simulator for Multicellu-  #
#     lar Systems, PLoS Comput. Biol. 14(2): e1005991, 2018                   #
#     DOI: 10.1371/journal.pcbi.1005991                                       #
#                                                                             #
# See VERSION.txt or call get_PhysiCell_version() to get the current version  #
#     x.y.z. Call display_citations() to get detailed information on all cite-#
#     able software used in your PhysiCell application.                       #
#                                                                             #
# Because PhysiCell extensively uses BioFVM, we suggest you also cite BioFVM  #
#     as below:                                                               #
#                                                                             #
# We implemented and solved the model using PhysiCell (Version x.y.z) [1],    #
# with BioFVM [2] to solve the transport equations.                           #
#                                                                             #
# [1] A Ghaffarizadeh, R Heiland, SH Friedman, SM Mumenthaler, and P Macklin, #
#     PhysiCell: an Open Source Physics-Based Cell Simulator for Multicellu-  #
#     lar Systems, PLoS Comput. Biol. 14(2): e1005991, 2018                   #
#     DOI: 10.1371/journal.pcbi.1005991                                       #
#                                                                             #
# [2] A Ghaffarizadeh, SH Friedman, and P Macklin, BioFVM: an efficient para- #
#     llelized diffusive transport solver for 3-D biological simulations,     #
#     Bioinformatics 32(8): 1256-8, 2016. DOI: 10.1093/bioinformatics/btv730  #
#                                                                             #
###############################################################################
#                                                                             #
# BSD 3-Clause License (see https://opensource.org/licenses/BSD-3-Clause)     #
#                                                                             #
# Copyright (c) 2015-2021, Paul Macklin and the PhysiCell Project             #
# All rights reserved.                                                        #
#                                                                             #
# Redistribution and use in source and binary forms, with or without          #
# modification, are permitted provided that the following conditions are met: #
#                                                                             #
# 1. Redistributions of source code must retain the above copyright notice,   #
# this list of conditions and the following disclaimer.                       #
#                                                                             #
# 2. Redistributions in binary form must reproduce the above copyright        #
# notice, this list of conditions and the following disclaimer in the         #
# documentation and/or other materials provided with the distribution.        #
#                                                                             #
# 3. Neither the name of the copyright holder nor the names of its            #
# contributors may be used to endorse or promote products derived from this   #
# software without specific prior written permission.                         #
#                                                                             #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" #
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE   #
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE  #
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE   #
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR         #
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF        #
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS    #
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN     #
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)     #
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE  #
# POSSIBILITY OF SUCH DAMAGE.                                                 #
#                                                                             #
###############################################################################
*/

#include "./custom.h"

void create_cell_types(void)
{
	// set the random seed 
	if (parameters.ints.find_index("random_seed") != -1)
	{
		SeedRandom(parameters.ints("random_seed"));
	}
	
	/*
	   Put any modifications to default cell definition here if you
	   want to have "inherited" by other cell types.

	   This is a good place to set default functions.
	*/

	initialize_default_cell_definition(); // in cell_ecm_interactions.cpp. Sets custom velocity function (cell-ECM motility interaction) and custom cell rule (ECM remodeling).cell_defaults.phenotype.secretion.sync_to_microenvironment( &microenvironment );
	cell_defaults.functions.volume_update_function = standard_volume_update_function;
	cell_defaults.functions.update_velocity = standard_update_cell_velocity;

	cell_defaults.functions.update_migration_bias = NULL;
	cell_defaults.functions.update_phenotype = NULL; // update_cell_and_death_parameters_O2_based;
	cell_defaults.functions.custom_cell_rule = NULL;
	cell_defaults.functions.contact_function = NULL;

	cell_defaults.functions.add_cell_basement_membrane_interactions = NULL;
	cell_defaults.functions.calculate_distance_to_membrane = NULL;

	// Custom data must exist on the default definition before XML inheritance;
	// otherwise MultiCellDS output sees inconsistent per-type layouts.
	xenophagy::register_petrinet_custom_data();

	/*
	   This parses the cell definitions in the XML config file.
	*/

	initialize_cell_definitions_from_pugixml();

	/*
	   This builds the map of cell definitions and summarizes the setup.
	*/

	build_cell_definitions_maps();

	/*
	   This intializes cell signal and response dictionaries
	*/

	setup_signal_behavior_dictionaries();

	/*
	   Cell rule definitions
	*/

	setup_cell_rules();

	/*
	   Put any modifications to individual cell definitions here.

	   This is a good place to set custom functions.
	*/

	cell_defaults.functions.update_phenotype = phenotype_function;
	cell_defaults.functions.contact_function = contact_function;

	// using biofvm to do ecm_density

	/*
	   This builds the map of cell definitions and summarizes the setup.
	*/

	display_cell_definitions(std::cout);

	// Attach the generated Petri-net only to tumor definitions and load the
	// optional manual entry schedule after all definitions are available.
	xenophagy::setup_petrinet_integration();

	return;
}

void setup_microenvironment(void)
{
	// set domain parameters

	// put any custom code to set non-homogeneous initial conditions or
	// extra Dirichlet nodes here.

	// initialize BioFVM

	initialize_microenvironment();

	return;
}

void setup_tissue()
{
	setup_tissue_domain();
	// load cells from your CSV file (if enabled)
	load_cells_from_pugixml();

	return;
}

void setup_tissue_domain(void)
{
	double Xmin = microenvironment.mesh.bounding_box[0];
	double Ymin = microenvironment.mesh.bounding_box[1];
	double Zmin = microenvironment.mesh.bounding_box[2];

	double Xmax = microenvironment.mesh.bounding_box[3];
	double Ymax = microenvironment.mesh.bounding_box[4];
	double Zmax = microenvironment.mesh.bounding_box[5];

	if (default_microenvironment_options.simulate_2D == true)
	{
		Zmin = 0.0;
		Zmax = 0.0;
	}

	double Xrange = Xmax - Xmin;
	double Yrange = Ymax - Ymin;
	double Zrange = Zmax - Zmin;
}

std::vector<std::string> my_coloring_function(Cell *pCell)
{
	// paint_by_number_cell_coloring() only has 13 colors (type index 0-12)
	// and silently falls back to white -- invisible on the white SVG
	// background -- for any type index >= 13. Adding cell types 9-16
	// (myCAF..NK_cell) pushed PMN_MDSC(13)/cDC1(14)/B_cell(15)/NK_cell(16)
	// past that limit, and fixed_vessel_source(17) hit it too. Types 0-12
	// keep the exact same colors as before (unchanged for the 9 original
	// pdac_therapy types + myCAF/iCAF/Treg/M_MDSC); 13-17 get explicit,
	// mutually distinct colors instead of the invisible white fallback.
	if( pCell->type < 13 )
	{ return paint_by_number_cell_coloring(pCell); }

	static std::vector<std::string> extra_colors = {
		"brown",      // 13: PMN_MDSC
		"purple",     // 14: cDC1
		"gold",       // 15: B_cell
		"teal",       // 16: NK_cell
		"black",      // 17: fixed_vessel_source
		"crimson",    // 18: fixed_vessel_source_compressed
		"lawngreen",  // 19: Bifidobacterium_longum
		"navy",       // 20: PD-L1lo_tumor_infected
		"deeppink",   // 21: PD-L1lo_tumor_xenophagy
		"sienna",     // 22: PD-L1hi_tumor_infected
		"turquoise"   // 23: PD-L1hi_tumor_xenophagy
	};
	std::string interior_color = "white";
	int extra_index = pCell->type - 13;
	if( extra_index >= 0 && extra_index < (int)extra_colors.size() )
	{ interior_color = extra_colors[extra_index]; }

	std::vector<std::string> output = { interior_color, "black", interior_color, "black" };
	return output;
}

// ---------------------------------------------------------------------------
// recruit_bacteria -- probabilistic Bifidobacterium longum entry near
// vessels, replacing the earlier bulk-seeded-at-t=0 approach per the
// user's correction: real translocation from blood is an ongoing,
// low-probability event per vessel, not a one-time bolus. Same Poisson-
// per-timestep pattern as PhysiCell_PDAC_TME's recruit_immune_cells:
// each vessel independently has probability lambda*dt of spawning one
// new bacterium nearby, each call. lambda is deliberately small
// ("进入数量极少") -- no literature value exists for translocation
// rate into a specific tumor, so this stays an adjustable placeholder,
// not a calibrated number.
// ---------------------------------------------------------------------------

void recruit_bacteria( double dt )
{
	static Cell_Definition* pBacteriaDef = find_cell_definition( "Bifidobacterium_longum" );
	static double lambda = parameters.doubles("bacteria_entry_lambda");

	std::vector<Cell*> vessels;
	for( int i=0; i < (*all_cells).size(); i++ )
	{
		Cell* pC = (*all_cells)[i];
		if( pC->phenotype.death.dead == true )
		{ continue; }
		if( pC->type_name == "fixed_vessel_source" || pC->type_name == "fixed_vessel_source_compressed" )
		{ vessels.push_back(pC); }
	}

	for( int i=0; i < vessels.size(); i++ )
	{
		if( UniformRandom() < lambda*dt )
		{
			Cell* pNew = create_cell( *pBacteriaDef );
			double angle = UniformRandom() * 6.283185307;
			double r = UniformRandom() * 30.0;
			std::vector<double> pos = vessels[i]->position;
			pos[0] += r*cos(angle);
			pos[1] += r*sin(angle);
			pNew->assign_position(pos);
		}
	}
	return;
}

// ---------------------------------------------------------------------------
// recruit_cd8_cells -- probabilistic CD8 T cell extravasation near vessels.
// Same Poisson-per-vessel-per-timestep pattern as recruit_bacteria, but the
// per-vessel rate is not constant: it is a Hill/Michaelis-Menten function of
// the current living-tumor-cell count,
//     lambda(N) = lambda_floor + (lambda_max - lambda_floor) * N/(N+K),
// so recruitment tapers toward a low ("persistent surveillance") floor as
// the tumor shrinks instead of staying fixed while a shrinking tumor faces
// an unchanging CD8 army -- addressing the literature-documented pattern
// that lymphoid content and tumor burden are coupled (e.g. "Tumor Size
// Matters", PMC7140082) and that antigen clearance drives ~90-95% effector
// T cell contraction within about a week (Nat. Immunol., Badovinac/Harty).
// lambda_max, lambda_floor, and K (the half-max tumor count) have no
// literature-measured values for this specific system -- they are adjustable
// placeholders chosen to be the same order of magnitude as bacteria_entry_
// lambda and the model's initial tumor/CD8 populations, not calibrated
// numbers.
// ---------------------------------------------------------------------------

void recruit_cd8_cells( double dt )
{
	static Cell_Definition* pCD8Def = find_cell_definition( "PD-1lo_CD137lo_CD8_Tcell" );
	static double lambda_max = parameters.doubles("cd8_recruitment_lambda_max");
	static double lambda_floor = parameters.doubles("cd8_recruitment_lambda_floor");
	static double K = parameters.doubles("cd8_recruitment_tumor_halfmax");
	static std::vector<std::string> tumor_type_names = {
		"PD-L1lo_tumor", "PD-L1hi_tumor",
		"PD-L1lo_tumor_infected", "PD-L1lo_tumor_xenophagy",
		"PD-L1hi_tumor_infected", "PD-L1hi_tumor_xenophagy"
	};

	int n_tumor = 0;
	std::vector<Cell*> vessels;
	for( int i=0; i < (*all_cells).size(); i++ )
	{
		Cell* pC = (*all_cells)[i];
		if( pC->phenotype.death.dead == true )
		{ continue; }
		if( pC->type_name == "fixed_vessel_source" || pC->type_name == "fixed_vessel_source_compressed" )
		{ vessels.push_back(pC); continue; }
		for( int k=0; k < (int)tumor_type_names.size(); k++ )
		{
			if( pC->type_name == tumor_type_names[k] )
			{ n_tumor++; break; }
		}
	}

	double lambda = lambda_floor + (lambda_max - lambda_floor) *
		(double)n_tumor / ( (double)n_tumor + K );

	for( int i=0; i < vessels.size(); i++ )
	{
		if( UniformRandom() < lambda*dt )
		{
			Cell* pNew = create_cell( *pCD8Def );
			double angle = UniformRandom() * 6.283185307;
			double r = UniformRandom() * 30.0;
			std::vector<double> pos = vessels[i]->position;
			pos[0] += r*cos(angle);
			pos[1] += r*sin(angle);
			pNew->assign_position(pos);
		}
	}
	return;
}

void phenotype_function(Cell *pCell, Phenotype &phenotype, double dt)
{
	xenophagy::petrinet_phenotype(pCell, phenotype, dt);
	return;
}

void custom_function(Cell *pCell, Phenotype &phenotype, double dt)
{
	return;
}

void contact_function(Cell *pMe, Phenotype &phenoMe, Cell *pOther, Phenotype &phenoOther, double dt)
{
	return;
}
