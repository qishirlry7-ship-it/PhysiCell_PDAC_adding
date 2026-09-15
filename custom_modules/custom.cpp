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

	// Gal-8/CD4 mechanism: per-bacterium carried-Gal8 amount, sampled at
	// creation time only for Bifidobacterium_longum_Gal8 instances (stays 0
	// on every other type, including plain Bifidobacterium_longum).
	if( cell_defaults.custom_data.find_variable_index( "gal8_amount" ) < 0 )
	{ cell_defaults.custom_data.add_variable( "gal8_amount", "a.u.", 0.0 ); }
	// How long (minutes) a CD4 T cell has been continuously exposed to
	// nonzero local Gal-8 -- the fitted CD4 dose-response is a function of
	// both concentration AND exposure duration (see cd4_gal8_proliferation_
	// rate() below), so this needs to persist and accumulate per-cell
	// across phenotype_function() calls, not be recomputed from scratch.
	if( cell_defaults.custom_data.find_variable_index( "gal8_exposure_time" ) < 0 )
	{ cell_defaults.custom_data.add_variable( "gal8_exposure_time", "min", 0.0 ); }

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

	// NOTE: initialize_cell_definitions_from_pugixml() (above) already
	// deep-copied cell_defaults -- including .functions, which was still
	// NULL at that point -- into every named Cell_Definition. Setting
	// cell_defaults.functions.update_phenotype here does NOT retroactively
	// reach any already-created type (same reason setup_petrinet_
	// integration() below has to assign petrinet_phenotype directly onto
	// each tumor Cell_Definition rather than relying on cell_defaults).
	// So the Gal-8/CD4 mechanism (inside phenotype_function) needs the same
	// explicit per-type wiring -- now on the 2 CD4 T-cell definitions
	// (moved from CD8; CD8's proliferation is Rules-driven via "contact
	// with PD-1lo_CD4_Tcell" in cell_rules.csv instead, since that's a
	// plain Hill function of a contact signal and doesn't need custom C++).
	{
		static const char* gal8_cd4_targets[] = {
			"PD-1lo_CD4_Tcell", "PD-1hi_CD4_Tcell"
		};
		for( const char* name : gal8_cd4_targets )
		{
			Cell_Definition* pCD = find_cell_definition( name );
			if( pCD )
			{ pCD->functions.update_phenotype = phenotype_function; }
		}
	}

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

	// initialize BioFVM

	initialize_microenvironment();

	// Overwrite the just-initialized uniform field with the actual saved
	// microenvironment state from checkpoint 88 (t=5280min, 3.67 days) of
	// the 45-day mechanism-4-only baseline run -- the population trough
	// (894 living tumor cells, smoothed-curve minimum, confirmed by a
	// sustained rise over the following 24h). This is real, spatially
	// varying field data (oxygen/glucose already locally depleted, not the
	// uniform 38/1.0 XML default), read via BioFVM's built-in
	// read_microenvironment_from_matlab(), which requires the voxel count
	// and substrate count/order to match exactly -- true here since this
	// is the same model/domain, just a different starting timepoint.
	read_microenvironment_from_matlab( "./config/ic_microenvironment/trough_microenvironment0.mat" );

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
		"turquoise",  // 23: PD-L1hi_tumor_xenophagy
		"white",      // 24: Bifidobacterium_longum_Gal8 (was falling through
		              //     to the same "white" default before this fix --
		              //     harmless but now explicit)
		"coral"       // 25: cDC1_licensed
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
	static Cell_Definition* pBacteriaGal8Def = find_cell_definition( "Bifidobacterium_longum_Gal8" );
	static double lambda = parameters.doubles("bacteria_entry_lambda");
	static bool bifido_enabled = parameters.bools("bifidobacterium_enabled");
	static bool bifido_gal8_enabled = parameters.bools("bifidobacterium_gal8_enabled");
	static double gal8_fixed_amount = parameters.doubles("gal8_amount_fixed");

	// Both switches default false (see user_parameters) -- skip the vessel
	// scan entirely unless at least one bacterium type is turned on.
	if( !bifido_enabled && !bifido_gal8_enabled )
	{ return; }

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
		if( bifido_enabled && UniformRandom() < lambda*dt )
		{
			Cell* pNew = create_cell( *pBacteriaDef );
			double angle = UniformRandom() * 6.283185307;
			double r = UniformRandom() * 30.0;
			std::vector<double> pos = vessels[i]->position;
			pos[0] += r*cos(angle);
			pos[1] += r*sin(angle);
			pNew->assign_position(pos);
		}

		if( bifido_gal8_enabled && UniformRandom() < lambda*dt )
		{
			Cell* pNew = create_cell( *pBacteriaGal8Def );
			double angle = UniformRandom() * 6.283185307;
			double r = UniformRandom() * 30.0;
			std::vector<double> pos = vessels[i]->position;
			pos[0] += r*cos(angle);
			pos[1] += r*sin(angle);
			pNew->assign_position(pos);

			// Every Gal8-carrying bacterium carries the same fixed amount
			// (no per-bacterium distribution -- see user_parameters
			// gal8_amount_fixed).
			pNew->custom_data["gal8_amount"] = gal8_fixed_amount;
		}
	}
	return;
}

// ---------------------------------------------------------------------------
// Pancreatic/gut hormone delivery (insulin, GLP-1, CCK). All three modeled
// as arriving via blood supply -- secreted by the same vessel points that
// already deliver oxygen/glucose. For insulin this is not just a modeling
// convenience: pancreatic islets are highly vascularized (~20% of arterial
// blood flow despite ~2% of pancreatic mass) and beta cells have polarized,
// directed secretion toward the capillary bed (see chat writeup for
// citations), so "arrives via blood" is a physiologically accurate
// description of how the tumor microenvironment actually encounters these
// hormones, not a shortcut. CCK is secreted by intestinal I-cells directly
// into the bloodstream in the same way (it is a classic circulating gut
// hormone, not locally produced in the pancreas itself), so the same vessel-
// delivery approach applies for the same underlying reason -- what matters
// for the tumor tissue is the concentration arriving via its blood supply,
// regardless of which organ made it.
//
// Each hormone's target local concentration (set as its vessels'
// secretion_target, i.e. phenotype.secretion.saturation_densities -- the
// concentration BioFVM's source term drives the local voxel toward) is:
//   target(t) = fasting_baseline * circadian(t) * (1 + (peak_fold-1)*pulse(t))
// circadian(t) is a mild +-hormone_circadian_amplitude sinusoid. For
// insulin/GLP-1: trough at 03:00, peak at 15:00 (literature: both are
// higher daytime/evening, lower overnight). For CCK: literature instead
// describes its circadian acrophase (peak) as falling in the DARK/night
// period -- the OPPOSITE phase from insulin/GLP-1 -- so CCK's circadian
// term is phase-shifted 12h (trough at 15:00, peak at 03:00) rather than
// reusing the same phase.
// pulse(t) sums 3 meal-triggered pulses/24h (08:00, 13:00, 19:00), each a
// normalized Bateman/biexponential rise-decay curve -- rise/decay time
// constants are hand-picked to match each hormone's literature-described
// qualitative timing (insulin: peaks ~25-30min, back near baseline by ~3h;
// GLP-1: peaks ~20min, back to baseline by ~3-4h; CCK: peaks ~20min --
// literature is explicit on this one, "peak within 20min" -- back near
// baseline by ~3-5h, the longest tail of the three, consistent with CCK
// staying elevated "until food empties from the stomach into the duodenum"),
// NOT fitted to precise PK rate constants (none were found in literature at
// this level of detail for any of the three). See chat writeup for the full
// citation list and the honest caveats on which fold-change numbers are
// direct literature ratios (GLP-1 40/15 pmol/L, CCK ~5/1 pM) vs rule-of-
// thumb placeholders (insulin's 5x).
// ---------------------------------------------------------------------------

static double bateman_pulse( double tau, double t_rise, double t_decay )
{
	if( tau < 0 )
	{ return 0.0; }
	double t_peak = (t_decay*t_rise)/(t_decay-t_rise) * log(t_decay/t_rise);
	double peak_val = exp(-t_peak/t_decay) - exp(-t_peak/t_rise);
	double val = exp(-tau/t_decay) - exp(-tau/t_rise);
	return val / peak_val;
}

static double meal_pulse_sum( double time_of_day_min, double t_rise, double t_decay )
{
	static const double meal_times[3] = { 480.0, 780.0, 1140.0 }; // 08:00, 13:00, 19:00
	double total = 0.0;
	for( int i=0; i < 3; i++ )
	{
		double tau = time_of_day_min - meal_times[i];
		if( tau < 0 )
		{ tau += 1440.0; } // most recent occurrence (possibly "yesterday's")
		total += bateman_pulse( tau, t_rise, t_decay );
	}
	return total;
}

void update_hormone_secretion( double dt )
{
	static int insulin_idx = microenvironment.find_density_index("insulin");
	static int glp1_idx = microenvironment.find_density_index("GLP1");
	static int cck_idx = microenvironment.find_density_index("CCK");

	static double insulin_fasting = parameters.doubles("insulin_fasting_pM");
	static double insulin_peak_fold = parameters.doubles("insulin_peak_fold");
	static double glp1_fasting = parameters.doubles("glp1_fasting_pM");
	static double glp1_peak_fold = parameters.doubles("glp1_peak_fold");
	static double cck_fasting = parameters.doubles("cck_fasting_pM");
	static double cck_peak_fold = parameters.doubles("cck_peak_fold");
	static double circadian_amp = parameters.doubles("hormone_circadian_amplitude");
	static double secretion_rate_const = parameters.doubles("hormone_secretion_rate");

	double time_of_day = fmod( PhysiCell_globals.current_time, 1440.0 );
	double circadian = 1.0 + circadian_amp * ( -cos( 6.28318530717959 * (time_of_day - 180.0) / 1440.0 ) );
	// CCK's literature-described acrophase is in the dark/night period --
	// the opposite phase from insulin/GLP-1 -- so shift by 12h (720 min).
	double circadian_cck = 1.0 + circadian_amp * ( -cos( 6.28318530717959 * (time_of_day - 180.0 + 720.0) / 1440.0 ) );

	double insulin_target = insulin_fasting * circadian *
		( 1.0 + (insulin_peak_fold - 1.0) * meal_pulse_sum(time_of_day, 15.0, 60.0) );
	double glp1_target = glp1_fasting * circadian *
		( 1.0 + (glp1_peak_fold - 1.0) * meal_pulse_sum(time_of_day, 8.0, 45.0) );
	double cck_target = cck_fasting * circadian_cck *
		( 1.0 + (cck_peak_fold - 1.0) * meal_pulse_sum(time_of_day, 8.0, 55.0) );

	for( int i=0; i < (*all_cells).size(); i++ )
	{
		Cell* pC = (*all_cells)[i];
		if( pC->phenotype.death.dead == true )
		{ continue; }
		if( pC->type_name == "fixed_vessel_source" || pC->type_name == "fixed_vessel_source_compressed" )
		{
			pC->phenotype.secretion.secretion_rates[insulin_idx] = secretion_rate_const;
			pC->phenotype.secretion.saturation_densities[insulin_idx] = insulin_target;
			pC->phenotype.secretion.secretion_rates[glp1_idx] = secretion_rate_const;
			pC->phenotype.secretion.saturation_densities[glp1_idx] = glp1_target;
			pC->phenotype.secretion.secretion_rates[cck_idx] = secretion_rate_const;
			pC->phenotype.secretion.saturation_densities[cck_idx] = cck_target;
		}
	}
	return;
}

// ---------------------------------------------------------------------------
// Gal-8/CD4 proliferation mechanism (agent-proximity). REDESIGNED this
// round: no longer touches CD8 killing at all (that multiplier is removed
// -- see cell_rules.csv's comment for the history). Gal-8 now acts on CD4 T
// cell PROLIFERATION, matching the user's own wet-lab CCK-8 assay, which
// measured CD4 viability/proliferation (not CD8) under Gal-8. CD8 gets its
// own, separate, CD4-contact-driven proliferation term instead (Rules-
// based, cell_rules.csv), representing CD4 "help" (literature: CD4-derived
// IL-2 licenses CD8 clonal expansion).
//
// Logic:
//   1. For each CD4 T cell, sum the gal8_amount of every living
//      Bifidobacterium_longum_Gal8 within gal8_effect_radius (no distance
//      weighting, unchanged from before).
//   2. Convert that raw sum to a LOCAL CONCENTRATION using the same
//      cylinder (not sphere) the user confirmed: radius = gal8_effect_radius
//      (20 micron, matches the existing bacterial_uptake_distance
//      convention), height = the model's own BioFVM mesh thickness dz (also
//      20 micron in this 2D-domain model) -- consistent with how every
//      other substrate's concentration in this model is defined, unlike a
//      true sphere which would extend past the domain's actual z-extent.
//      C[uM] = raw[molecules] / (602.2 * V[um^3])   (602.2 = N_A*1e-15*1e-6,
//      i.e. Avogadro's number times the L-per-um^3 and M-per-uM factors)
//      NOTE: gal8_amount is still in placeholder "a.u.", not real molecule
//      counts (pending the collaborator's E_required distribution -- see
//      chat), so this conversion is dimensionally correct but not yet
//      numerically calibrated; see the chat writeup for the resulting
//      concentration-scale mismatch against the CCK-8-tested 0.05-0.5 uM
//      range.
//   3. Track gal8_exposure_time (minutes) per CD4 cell: increments while
//      locally-sensed raw Gal-8 > 0, resets to 0 the instant it drops back
//      to 0 -- the fitted dose-response is a function of both concentration
//      AND continuous exposure duration (see below).
//   4. Net relative cycle-entry-rate perturbation, fit (least squares, pure
//      Python, no scipy in this environment) to the user's two CD4 CCK-8
//      files (Row A = 24h, Row B = 44h culture; 0.05/0.2/0.5 uM; viability
//      already normalized to same-timepoint 0 uM control in the source
//      data):
//        r(C,t) = Pmax*C/(C+Kp) - Irate*t*C/(C+Ki)      [t in hours]
//      Pmax*C/(C+Kp) is a fast-saturating PROMOTION term (captures the
//      24h low-dose boost -- literature: low-dose Gal-8 T-cell
//      costimulation). Irate*t*C/(C+Ki) is an INHIBITION term whose
//      effective ceiling grows linearly with exposure time (captures the
//      24h->44h flip from net-promotion to net-decline at low dose, and
//      the much steeper drop at 44h than 24h at 0.5uM -- literature:
//      sustained/high Gal-8 exposure is pro-apoptotic via a pathway that
//      plausibly needs time to build up). Fit quality: R^2=0.92 across the
//      6 (dose,time) points; the single biggest miss is 0.05uM/24h, which
//      is also the single highest-SD point in the source data (SD=21.9%)
//      -- see chat for the full fit table.
//   5. UPDATED (superseding the original "proliferation only" scope): r(C,t)
//      is now read as a NET relative growth rate -- exactly what it was
//      fit from (ln(viability ratio)/t is birth rate minus death rate,
//      lumped together, since CCK-8 endpoint OD cannot separate them). It
//      is split at the population-dynamics level, the same way a net growth
//      rate is conventionally decomposed into its birth and death halves:
//        r >= 0:  cycle_entry_rate = r/60   (1/h -> 1/min), apoptosis stays
//                 at CD4's baseline (0, XML)
//        r <  0:  cycle_entry_rate = 0, apoptosis_rate = -r/60
//      So above whatever concentration/exposure-time combination makes
//      r(C,t) cross 0, CD4 stops dividing AND starts dying at a rate equal
//      in magnitude to how far r has gone negative -- i.e. the same fitted
//      curve now drives death instead of being clamped away. This is a
//      closer match to what the CCK-8 data actually measured (net viable
//      count) than the earlier "proliferation-only, clamp at 0" version.
// ---------------------------------------------------------------------------

static double sum_nearby_gal8( Cell* pCell, double radius )
{
	int voxel = pCell->get_current_mechanics_voxel_index();
	if( voxel < 0 )
	{ return 0.0; }

	double radius2 = radius*radius;
	double total = 0.0;

	std::vector<int> voxels(1, voxel);
	const std::vector<int>& adjacent = pCell->get_container()->underlying_mesh.moore_connected_voxel_indices[voxel];
	voxels.insert( voxels.end(), adjacent.begin(), adjacent.end() );

	for( int candidate_voxel : voxels )
	{
		for( Cell* candidate : pCell->get_container()->agent_grid[candidate_voxel] )
		{
			if( candidate->phenotype.death.dead || candidate->phenotype.flagged_for_removal )
			{ continue; }
			if( candidate->type_name != "Bifidobacterium_longum_Gal8" )
			{ continue; }

			double dx = pCell->position[0] - candidate->position[0];
			double dy = pCell->position[1] - candidate->position[1];
			double dz = pCell->position[2] - candidate->position[2];
			double d2 = dx*dx + dy*dy + dz*dz;
			if( d2 > radius2 )
			{ continue; }

			total += candidate->custom_data["gal8_amount"];
		}
	}
	return total;
}

// Net relative growth rate (1/min, signed) -- positive means "net
// proliferation", negative means "net decline". See point 5 above for how
// phenotype_function() splits this into cycle-entry vs apoptosis rates.
static double cd4_gal8_net_growth_rate( double raw_gal8, double exposure_time_min )
{
	static double radius = parameters.doubles("gal8_effect_radius");
	static double V_cyl  = 3.14159265358979 * radius * radius * microenvironment.mesh.dz;
	static double Pmax  = parameters.doubles("cd4_gal8_prolif_Pmax");
	static double Kp    = parameters.doubles("cd4_gal8_prolif_Kp");
	static double Irate = parameters.doubles("cd4_gal8_prolif_Irate");
	static double Ki    = parameters.doubles("cd4_gal8_prolif_Ki");

	double C_uM = raw_gal8 / (602.2 * V_cyl);
	double t_hours = exposure_time_min / 60.0;

	double r = Pmax * C_uM/(C_uM + Kp) - Irate * t_hours * C_uM/(C_uM + Ki);

	return r / 60.0; // 1/h -> 1/min
}

void phenotype_function(Cell *pCell, Phenotype &phenotype, double dt)
{
	xenophagy::petrinet_phenotype(pCell, phenotype, dt);

	// Gal-8-driven proliferation on CD4 T cells: DISABLED by default (user
	// request), gated on its own independent switch (gal8_cd4_effect_
	// enabled) rather than on bifidobacterium_gal8_enabled. This
	// deliberately decouples "does the Gal-8-carrying bacterium exist" from
	// "does Gal-8 concentration do anything to T cells" -- with this switch
	// off, Bifidobacterium_longum_Gal8 can be spawned (bifidobacterium_
	// gal8_enabled=true) and carry gal8_amount same as before, but no CD4
	// cell ever reads nearby Gal-8 or has its cycle-entry/apoptosis rate
	// touched by it: sum_nearby_gal8() is never called for this purpose,
	// gal8_exposure_time never accumulates, cd4_gal8_net_growth_rate() is
	// never evaluated. Nothing below this switch check runs. Code kept
	// in place, not deleted, so it can be re-enabled by flipping the one
	// switch in user_parameters.
	static bool gal8_cd4_effect_enabled = parameters.bools("gal8_cd4_effect_enabled");
	if( gal8_cd4_effect_enabled &&
		( pCell->type_name == "PD-1lo_CD4_Tcell" || pCell->type_name == "PD-1hi_CD4_Tcell" ) )
	{
		static double radius = parameters.doubles("gal8_effect_radius");
		double raw = sum_nearby_gal8( pCell, radius );

		double& texp = pCell->custom_data["gal8_exposure_time"];
		if( raw > 1e-12 )
		{ texp += dt; }
		else
		{ texp = 0.0; }

		double r = cd4_gal8_net_growth_rate( raw, texp );

		static int apoptosis_index = phenotype.death.find_death_model_index( "apoptosis" );
		if( r >= 0 )
		{
			phenotype.cycle.data.transition_rate(0,0) = r;
			phenotype.death.rates[apoptosis_index] = 0.0;
		}
		else
		{
			phenotype.cycle.data.transition_rate(0,0) = 0.0;
			phenotype.death.rates[apoptosis_index] = -r;
		}
	}

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
