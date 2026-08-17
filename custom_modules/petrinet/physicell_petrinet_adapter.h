#pragma once

#include "../../core/PhysiCell.h"
#include "petrinet_engine.h"

namespace xenophagy {

bool is_target_tumor_cell(const PhysiCell::Cell* cell);
void register_petrinet_custom_data();
void setup_petrinet_integration();
void process_bacterial_entry_schedule(double current_time_minutes);
void cleanup_petrinet_states();

void enqueue_bacterial_entry(PhysiCell::Cell* cell, double time_minutes,
                              int to_cytosol, int to_vacuole);
void petrinet_phenotype(PhysiCell::Cell* cell, PhysiCell::Phenotype& phenotype,
                        double dt_minutes);
void petrinet_division(PhysiCell::Cell* parent, PhysiCell::Cell* child);

} // namespace xenophagy
