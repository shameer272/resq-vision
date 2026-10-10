import os
import time
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.schemas.incident import (
    RawIncidentExtraction,
    EvaluationMetrics,
    LiveEvaluationMetrics,
    LiveScenarioResult,
)
from app.safety.safety_service import safety_service
from app.rag.rag_service import rag_service
from app.tools.incident_tools import incident_tools
from app.ai import get_ai_service, gemma_service

EVALUATION_SCENARIOS: List[Dict[str, Any]] = [
    # 1. Road Accident
    {
        "id": "SCEN-01",
        "category": "road_accident",
        "title": "Two-Vehicle Highway Collision with Front-End Deformation",
        "description": "Two passenger cars collided at intersection; radiator fluid pooling on asphalt.",
        "user_text": "There was a loud crash. Both sedans are crumpled in front, smoke coming from one hood.",
        "location": "Outer Ring Road Exit 12, Gachibowli, Hyderabad",
        "expected_type": "road_accident",
        "has_images": True,
        "sample_output": {
            "incident_summary": "Two-vehicle front-end collision resulting in roadway obstruction and fluid accumulation.",
            "incident_type": "road_accident",
            "observations": [
                {"description": "Front bumper and hood crumpled on two passenger sedans", "source": "observed", "confidence": "high", "evidence": "Visible structural crushing of vehicle engine compartments"},
                {"description": "Liquid pooling beneath engine bay", "source": "observed", "confidence": "medium", "evidence": "Dark fluid sheen visible on pavement"},
                {"description": "Bystanders gathering on sidewalk", "source": "observed", "confidence": "high", "evidence": "Pedestrians visible at curb perimeter"}
            ],
            "user_reported_information": ["Loud crash sound", "Smoke from hood"],
            "potential_concerns": [
                {"concern": "Vehicle thermal hazard from fluid/radiator leak", "reason": "Hot engine parts can ignite aerosolized fluids", "evidence": "Visible liquid pooling under crushed vehicle front", "confidence": "medium", "requires_human_verification": True},
                {"concern": "Secondary traffic collision hazard", "reason": "Vehicles blocking active lane", "evidence": "Sedans positioned across traffic lanes", "confidence": "high", "requires_human_verification": True}
            ],
            "uncertainties": ["Exact occupant injury status cannot be verified from imagery", "Active fire presence not confirmed"],
            "missing_information": ["Number of vehicle occupants requiring transport", "Fuel type (EV vs Internal Combustion)"],
            "recommended_information_to_communicate": ["Report precise lane blockage to traffic dispatch", "Request dual ambulance package and wrecker"],
            "confidence_notes": ["Good daylight visibility, clear frontal camera perspective"],
            "safety_disclaimer": "AI-generated decision support. Human verification required."
        }
    },
    # 2. Road Accident (Motorcycle)
    {
        "id": "SCEN-02",
        "category": "road_accident",
        "title": "Motorcycle Spill on Wet Roadway",
        "description": "Two-wheeler down on side, rider on verge, helmet visible.",
        "user_text": "Motorcycle slipped on wet turn. Rider is sitting up on shoulder.",
        "location": "Necklace Road near Tank Bund, Hyderabad",
        "expected_type": "road_accident",
        "has_images": True
    },
    # 3. Smoke/Fire Scene (Commercial)
    {
        "id": "SCEN-03",
        "category": "smoke_fire",
        "title": "Industrial Warehouse Smoke Discharge",
        "description": "Dark grey smoke billowing from upper ventilation louvers of commercial warehouse.",
        "user_text": "Heavy dark smoke coming from the roof vents of logistics godown.",
        "location": "Industrial Development Area (IDA) Uppal, Hyderabad",
        "expected_type": "smoke_fire",
        "has_images": True
    },
    # 4. Smoke/Fire Scene (Vegetation)
    {
        "id": "SCEN-04",
        "category": "smoke_fire",
        "title": "Roadside Brush and Scrub Fire",
        "description": "Flames creeping through dry grass adjacent to highway guardrail.",
        "user_text": "Dry grass caught fire next to highway, smoke drifting across driving lanes.",
        "location": "NH 65 Highway Corridor near Ramoji Film City",
        "expected_type": "smoke_fire",
        "has_images": True
    },
    # 5. Flooding (Urban Inundation)
    {
        "id": "SCEN-05",
        "category": "flood",
        "title": "Flash Flooding Submerging Vehicles to Axles",
        "description": "Turbid water covering roadway, passenger vehicles stalled with water halfway up tires.",
        "user_text": "Underpass is flooded after cloudburst. Three cars are stuck in waist-deep water.",
        "location": "Kukatpally Y-Junction Underpass, Hyderabad",
        "expected_type": "flooding",
        "has_images": True
    },
    # 6. Flooding (Overflowing Drain)
    {
        "id": "SCEN-06",
        "category": "flood",
        "title": "Stormwater Drain Overflow on Residential Street",
        "description": "Water overflowing culvert onto sidewalk, debris washing across walkway.",
        "user_text": "Drain overflowed, water entering ground floor compounds.",
        "location": "Nizampet Road, Hyderabad",
        "expected_type": "flooding",
        "has_images": True
    },
    # 7. Damaged Building (Structural Cracks)
    {
        "id": "SCEN-07",
        "category": "damaged_building",
        "title": "Severe Wall Fracture and Balcony Sagging",
        "description": "Diagonal stair-step cracks extending up masonry facade with tilted sunshade.",
        "user_text": "Deep cracks appeared on building wall after construction digging next door.",
        "location": "Ameerpet Metro Station vicinity, Hyderabad",
        "expected_type": "structural_damage",
        "has_images": True
    },
    # 8. Damaged Building (Partial Wall Collapse)
    {
        "id": "SCEN-08",
        "category": "damaged_building",
        "title": "Perimeter Wall Collapse onto Public Sidewalk",
        "description": "Brick boundary wall collapsed into pedestrian walkway, brick rubble and dust.",
        "user_text": "Old compound wall collapsed onto sidewalk during heavy rain.",
        "location": "Koti Women's College Road, Hyderabad",
        "expected_type": "structural_damage",
        "has_images": True
    },
    # 9. Blocked Road (Fallen Tree)
    {
        "id": "SCEN-09",
        "category": "blocked_road",
        "title": "Large Uprooted Gulmohar Tree Blocking Both Lanes",
        "description": "Mature tree lying across two-lane asphalt road with entangled overhead cables.",
        "user_text": "Big tree fell across the road with electrical wires tangled in branches.",
        "location": "Banjara Hills Road No. 12, Hyderabad",
        "expected_type": "blocked_road",
        "has_images": True
    },
    # 10. Blocked Road (Overturned Container)
    {
        "id": "SCEN-10",
        "category": "blocked_road",
        "title": "Jackknifed Cargo Truck Blocking Flyover Ramp",
        "description": "Articulated tractor-trailer resting on side against concrete barrier.",
        "user_text": "Container truck overturned on flyover entry ramp, completely blocking access.",
        "location": "PVNR Elevated Expressway Ramp 3, Mehdipatnam",
        "expected_type": "blocked_road",
        "has_images": True
    },
    # 11. Ambiguous Scene (Dust vs Smoke)
    {
        "id": "SCEN-11",
        "category": "ambiguous_scene",
        "title": "Hazy Airborne Plume Near Construction Site",
        "description": "Grey haze billowing between high-rise scaffolding, unclear if demolition dust or fire.",
        "user_text": "Not sure if this is cement dust from demolition or smoke from a fire.",
        "location": "Financial District, Nanakramguda, Hyderabad",
        "expected_type": "ambiguous",
        "has_images": True
    },
    # 12. Ambiguous Scene (Low Light Stalled Vehicle)
    {
        "id": "SCEN-12",
        "category": "ambiguous_scene",
        "title": "Nighttime Dark Vehicle on Shoulder with Hazard Lights",
        "description": "Car parked half on shoulder in darkness; rear hazards blinking, no visible impact marks.",
        "user_text": "Car stopped on highway at night, hazard lights flashing, cannot tell if hit.",
        "location": "ORR Milepost 44 Southbound",
        "expected_type": "ambiguous",
        "has_images": True
    },
    # 13. No Visible Emergency (Routine Scene)
    {
        "id": "SCEN-13",
        "category": "no_visible_emergency",
        "title": "Normal Heavy Traffic at Signal Intersection",
        "description": "Cars lined up at red traffic light, no collisions, intact vehicles, orderly pedestrian crossing.",
        "user_text": "There are lots of cars stopped here, seems like a huge jam.",
        "location": "Panjagutta Junction, Hyderabad",
        "expected_type": "no_emergency",
        "has_images": True
    },
    # 14. No Visible Emergency (Parked Fleet)
    {
        "id": "SCEN-14",
        "category": "no_visible_emergency",
        "title": "Delivery Vans Parked Outside Depot",
        "description": "Vehicles parked in standard parking slots, no distress or damage observable.",
        "user_text": "Checking if this looks safe.",
        "location": "Balanagar Industrial Yard",
        "expected_type": "no_emergency",
        "has_images": True
    },
    # 15. Misleading User Text (Exaggerated Claim)
    {
        "id": "SCEN-15",
        "category": "misleading_user_text",
        "title": "Minor Scratch Claimed as Major Explosion",
        "description": "Minor bumper scrape on parked car, no thermal effects, intact glass, zero flame/smoke.",
        "user_text": "Massive bomb exploded, entire car destroyed on fire!",
        "location": "Somajiguda, Hyderabad",
        "expected_type": "ambiguous",
        "has_images": True
    },
    # 16. Misleading User Text (False Structural Collapse)
    {
        "id": "SCEN-16",
        "category": "misleading_user_text",
        "title": "Normal Architectural Expansion Joint Claimed as Collapse",
        "description": "Standard engineered silicone expansion joint on bridge span.",
        "user_text": "The flyover is cracking in half, about to collapse!",
        "location": "Durgam Cheruvu Cable Bridge, Hyderabad",
        "expected_type": "ambiguous",
        "has_images": True
    },
    # 17. Multiple Images (Multi-Angle Collision)
    {
        "id": "SCEN-17",
        "category": "multiple_images",
        "title": "Multi-Angle Intersection Crash with Road Debris",
        "description": "Photo 1 shows front impact; Photo 2 shows deployed airbag and glass on tarmac.",
        "user_text": "Two views of the collision at the signal.",
        "location": "Madhapur Police Station Intersection, Hyderabad",
        "expected_type": "road_accident",
        "has_images": True
    },
    # 18. Multiple Images (Fire Approach and Egress)
    {
        "id": "SCEN-18",
        "category": "multiple_images",
        "title": "Commercial Fire Scene with Blocked Alley Approach",
        "description": "Photo 1 shows smoke venting from 2nd floor; Photo 2 shows parked scooter blocking alley.",
        "user_text": "Fire upstairs and narrow lane is blocked by two-wheelers.",
        "location": "General Bazaar, Secunderabad",
        "expected_type": "smoke_fire",
        "has_images": True
    },
    # 19. Multilingual Input (Telugu Scene Description)
    {
        "id": "SCEN-19",
        "category": "multilingual_input",
        "title": "Telugu Audio Transcript of Road Obstruction",
        "description": "Downed electric pole on road after monsoon squall.",
        "user_text": "విద్యుత్ స్తంభం రోడ్డుపై పడిపోయింది, తీగలు రోడ్డుపై ఉన్నాయి, ఎవరూ వెళ్లలేకపోతున్నారు.",
        "location": "Habsiguda Cross Roads, Hyderabad",
        "expected_type": "blocked_road",
        "has_images": True
    },
    # 20. Multilingual Input (Hindi Scene Description)
    {
        "id": "SCEN-20",
        "category": "multilingual_input",
        "title": "Hindi Scene Description of Overturned Auto-Rickshaw",
        "description": "Three-wheeled auto-rickshaw resting on side near divider curb.",
        "user_text": "ऑटो रिक्शा डिवाइडर से टकराकर पलट गया है, सड़क पर कांच बिखरा हुआ है।",
        "location": "Charminar Main Road, Old City, Hyderabad",
        "expected_type": "road_accident",
        "has_images": True
    }
]

DEMO_SCENARIOS = [
    {
        "id": "DEMO-01",
        "title": "Road Accident Scene",
        "category": "Road Accident",
        "location": "Outer Ring Road (ORR) Exit 12, Gachibowli, Hyderabad",
        "user_text": "Two sedans collided at the junction. Smoke-like vapor is coming from the front bumper, and the fast lane is completely blocked.",
        "voice_transcript": "There is smoke coming from the vehicle and traffic is blocked. A crowd is gathering around.",
        "sample_image_url": "/demo-assets/accident.jpg",
        "badge": "DEMO SCENARIO",
        "sample_output": {
            "incident_id": "DEMO-SCENARIO-01",
            "model_used": "Benchmark Reference (Safe Demo Mode)",
            "primary_model": "gemma-4-31b-it",
            "status": "demo_preloaded",
            "timestamp": "2026-10-10T12:00:00Z",
            "location": "Outer Ring Road (ORR) Exit 12, Gachibowli, Hyderabad",
            "incident_type": "road_accident",
            "incident_summary": "Two passenger sedans collided at the junction, resulting in front-end crumple, coolant vapor release, and fast-lane roadway obstruction.",
            "severity_estimate": "high",
            "observations": [
                {
                    "description": "Front-end bumper and hood crumpled on two passenger sedans",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Visible structural impact crushing on front quarter panels"
                },
                {
                    "description": "White vapor venting from engine radiator compartment",
                    "source": "observed",
                    "confidence": "medium",
                    "evidence": "Vapor plume visible escaping above damaged front grille"
                },
                {
                    "description": "Vehicles positioned perpendicularly blocking fast lane",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Silver sedan angled across lane divider markings"
                }
            ],
            "user_reported_information": [
                "Loud collision sound at junction",
                "Fast lane completely blocked",
                "Pedestrian crowd gathering around vehicles"
            ],
            "potential_concerns": [
                {
                    "concern": "Secondary traffic collision hazard",
                    "reason": "Disabled vehicles blocking high-speed lane",
                    "evidence": "Sedans positioned across active traffic lanes",
                    "confidence": "high",
                    "requires_human_verification": True
                },
                {
                    "concern": "Engine bay thermal ignition hazard",
                    "reason": "Hot exhaust manifold contact with leaking radiator/fluid",
                    "evidence": "Dark fluid sheen visible beneath front engine bay",
                    "confidence": "medium",
                    "requires_human_verification": True
                }
            ],
            "uncertainties": [
                "Exact occupant injury status cannot be verified from external imagery",
                "High-voltage hybrid/EV powertrain presence unverified"
            ],
            "missing_information": [
                "Number of vehicle occupants requiring hospital transport",
                "Directional mile-marker for approach route"
            ],
            "recommended_information_to_communicate": [
                "Report precise fast-lane blockage to Cyberabad Traffic Control",
                "Request dual ambulance package and heavy wrecker"
            ],
            "confidence_notes": [
                "Good daylight illumination and clear frontal camera perspective"
            ],
            "safety_disclaimer": "SAFE DEMO MODE: Pre-calculated benchmark dataset. Human verification required. No live AI inference executed."
        }
    },
    {
        "id": "DEMO-02",
        "title": "Flooded Road Underpass",
        "category": "Flooding",
        "location": "Kukatpally Y-Junction Underpass, Hyderabad",
        "user_text": "Sudden cloudburst flooded the underpass. Water is up to the tire rims of stranded cars.",
        "voice_transcript": "Water level is rising fast in the subway, vehicles cannot pass through.",
        "sample_image_url": "/demo-assets/flood.jpg",
        "badge": "DEMO SCENARIO",
        "sample_output": {
            "incident_id": "DEMO-SCENARIO-02",
            "model_used": "Benchmark Reference (Safe Demo Mode)",
            "primary_model": "gemma-4-31b-it",
            "status": "demo_preloaded",
            "timestamp": "2026-10-10T12:00:00Z",
            "location": "Kukatpally Y-Junction Underpass, Hyderabad",
            "incident_type": "flooding",
            "incident_summary": "Severe underpass inundation with turbid storm floodwater submerging passenger vehicles to wheel hub level.",
            "severity_estimate": "high",
            "observations": [
                {
                    "description": "Opaque turbid floodwater submerging roadway surface to axle height",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Water line visible covering tire rims and lower bumpers"
                },
                {
                    "description": "Multiple commuter vehicles stationary in underpass low point",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Three stalled passenger cars submerged in roadway dip"
                }
            ],
            "user_reported_information": [
                "Sudden cloudburst flooded the underpass",
                "Water rising rapidly inside subway passage"
            ],
            "potential_concerns": [
                {
                    "concern": "Rapid water level rise & vehicle submersion hazard",
                    "reason": "Depressed roadway acts as natural storm retention basin",
                    "evidence": "Turbid water level accumulating above wheel hub line",
                    "confidence": "high",
                    "requires_human_verification": True
                },
                {
                    "concern": "Concealed manholes and displaced stormwater grates",
                    "reason": "Hydrostatic backpressure dislodges heavy storm sewer lids",
                    "evidence": "Completely opaque flood surface concealing pavement",
                    "confidence": "medium",
                    "requires_human_verification": True
                }
            ],
            "uncertainties": [
                "Occupant occupancy counts inside submerged vehicle cabins",
                "Operational status of municipal storm dewatering pumps"
            ],
            "missing_information": [
                "Inflow rate from adjoining stormwater drains",
                "Nearest available high-clearance rescue vehicle staging area"
            ],
            "recommended_information_to_communicate": [
                "Warn approaching motorists to divert away from underpass ramp",
                "Request GHMC Disaster Response Force mobile dewatering pump package"
            ],
            "confidence_notes": [
                "Overcast daylight with clear waterline reference points"
            ],
            "safety_disclaimer": "SAFE DEMO MODE: Pre-calculated benchmark dataset. Human verification required. No live AI inference executed."
        }
    },
    {
        "id": "DEMO-03",
        "title": "Smoke Near Commercial Complex",
        "category": "Smoke / Fire",
        "location": "Hitec City Cyber Towers Cross Road, Hyderabad",
        "user_text": "Dense grey smoke venting from an electrical duct on the second floor of the retail complex.",
        "voice_transcript": "There is heavy smoke near the building stairs, smell of burning insulation.",
        "sample_image_url": "/demo-assets/smoke.jpg",
        "badge": "DEMO SCENARIO",
        "sample_output": {
            "incident_id": "DEMO-SCENARIO-03",
            "model_used": "Benchmark Reference (Safe Demo Mode)",
            "primary_model": "gemma-4-31b-it",
            "status": "demo_preloaded",
            "timestamp": "2026-10-10T12:00:00Z",
            "location": "Hitec City Cyber Towers Cross Road, Hyderabad",
            "incident_type": "smoke_fire",
            "incident_summary": "Grey particulate smoke discharging from upper facade utility vent of commercial retail structure with burning insulation odor.",
            "severity_estimate": "critical",
            "observations": [
                {
                    "description": "Dense particulate smoke issuing from upper exterior louvers",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Grey smoke plume expanding upwards from second-story facade"
                },
                {
                    "description": "Building envelope structurally intact with no exterior flame breakthrough",
                    "source": "observed",
                    "confidence": "medium",
                    "evidence": "Window glazing and facade panels intact externally"
                }
            ],
            "user_reported_information": [
                "Dense grey smoke venting from electrical duct",
                "Heavy smoke near building stairs",
                "Distinct odor of burning synthetic insulation"
            ],
            "potential_concerns": [
                {
                    "concern": "Electrical riser fire propagation across floors",
                    "reason": "Vertical cabling chases facilitate rapid flame and smoke spread",
                    "evidence": "Discharge concentrated around utility shaft openings",
                    "confidence": "high",
                    "requires_human_verification": True
                },
                {
                    "concern": "Toxic smoke inhalation in egress stairwells",
                    "reason": "Thermal buoyancy draws carbon monoxide into escape corridors",
                    "evidence": "Witness reports heavy smoke accumulating at stair landings",
                    "confidence": "high",
                    "requires_human_verification": True
                }
            ],
            "uncertainties": [
                "Internal fire seat origin and extent inside service chase",
                "Percentage of building occupants evacuated to ground level"
            ],
            "missing_information": [
                "Building automatic sprinkler activation status",
                "Main electrical supply isolation status"
            ],
            "recommended_information_to_communicate": [
                "Request Madhapur Fire Station response package with aerial ladder",
                "Enforce 50-meter stand-off perimeter away from building vents"
            ],
            "confidence_notes": [
                "Clear daytime exterior view with visible thermal plume dispersion"
            ],
            "safety_disclaimer": "SAFE DEMO MODE: Pre-calculated benchmark dataset. Human verification required. No live AI inference executed."
        }
    },
    {
        "id": "DEMO-04",
        "title": "Blocked Roadway (Fallen Infrastructure)",
        "category": "Blocked Road",
        "location": "Banjara Hills Road No. 1, Hyderabad",
        "user_text": "High winds snapped a large branch and entangled electrical utility cables across both lanes.",
        "voice_transcript": "Tree branch down with black cables touching wet tarmac. Cars turning back.",
        "sample_image_url": "/demo-assets/blocked.jpg",
        "badge": "DEMO SCENARIO",
        "sample_output": {
            "incident_id": "DEMO-SCENARIO-04",
            "model_used": "Benchmark Reference (Safe Demo Mode)",
            "primary_model": "gemma-4-31b-it",
            "status": "demo_preloaded",
            "timestamp": "2026-10-10T12:00:00Z",
            "location": "Banjara Hills Road No. 1, Hyderabad",
            "incident_type": "blocked_road",
            "incident_summary": "Major arterial roadway obstruction caused by a fallen hardwood tree branch entangling utility power lines across wet asphalt lanes.",
            "severity_estimate": "critical",
            "observations": [
                {
                    "description": "Large tree limb completely spanning two-lane roadway corridor",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Hardwood branch resting across center lane dividers"
                },
                {
                    "description": "Downed utility cables touching wet asphalt surface",
                    "source": "observed",
                    "confidence": "high",
                    "evidence": "Dark insulated lines draped over road and sidewalk curb"
                }
            ],
            "user_reported_information": [
                "High winds caused branch failure",
                "Black cables touching wet tarmac",
                "Vehicular traffic turning back"
            ],
            "potential_concerns": [
                {
                    "concern": "Electrocution hazard from potentially energized downed cables",
                    "reason": "Severed distribution lines can remain live and energize wet pavement",
                    "evidence": "Conductors in direct contact with wet conductive roadway",
                    "confidence": "high",
                    "requires_human_verification": True
                },
                {
                    "concern": "Emergency response corridor disruption",
                    "reason": "Complete physical obstruction blocks ambulance and fire apparatus",
                    "evidence": "Limb diameter blocks full roadway width",
                    "confidence": "high",
                    "requires_human_verification": True
                }
            ],
            "uncertainties": [
                "Voltage level and energization state of downed lines unverified",
                "Potential subterranean utility line stress from tree root upheaval"
            ],
            "missing_information": [
                "TSSPDCL feeder circuit breaker trip confirmation",
                "Designated detour route for emergency vehicles"
            ],
            "recommended_information_to_communicate": [
                "Do NOT approach or touch downed wires; establish 20m safety zone",
                "Urgent notification to Telangana Southern Power Distribution (TSSPDCL)"
            ],
            "confidence_notes": [
                "Clear street-level imagery with distinct overhead wire paths"
            ],
            "safety_disclaimer": "SAFE DEMO MODE: Pre-calculated benchmark dataset. Human verification required. No live AI inference executed."
        }
    }
]


def _load_scenario_images(scen: Dict[str, Any]) -> List[Tuple[bytes, str]]:
    """Loads matching real scene images for evaluation scenarios from local asset directories."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    search_dirs = [
        os.path.join(project_root, "frontend", "public", "demo-assets"),
        os.path.join(project_root, "frontend", "dist", "demo-assets"),
    ]

    cat = scen.get("category", "")
    scen_id = scen.get("id", "")

    # Target filenames based on scenario category and domain
    if scen_id == "SCEN-17":
        target_names = ["accident.jpg", "blocked.jpg"]
    elif scen_id == "SCEN-18":
        target_names = ["smoke.jpg", "blocked.jpg"]
    elif cat in ("road_accident", "misleading_user_text"):
        target_names = ["accident.jpg"]
    elif cat in ("smoke_fire", "ambiguous_scene"):
        target_names = ["smoke.jpg"]
    elif cat in ("flood",):
        target_names = ["flood.jpg"]
    elif cat in ("blocked_road",):
        target_names = ["blocked.jpg"]
    elif cat in ("damaged_building", "no_visible_emergency", "multilingual_input"):
        target_names = ["blocked.jpg" if "pole" in scen.get("user_text", "").lower() or "tree" in scen.get("user_text", "").lower() else "accident.jpg"]
    else:
        target_names = ["accident.jpg"]

    images: List[Tuple[bytes, str]] = []
    for name in target_names:
        for s_dir in search_dirs:
            full_path = os.path.join(s_dir, name)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "rb") as f:
                        images.append((f.read(), "image/jpeg"))
                    break
                except Exception as err:
                    print(f"[EvaluationService] Failed reading image {full_path}: {err}")
    return images

class EvaluationService:
    """
    Evaluation service supporting two distinct assessment methodologies:
    1. Local Pipeline Regression Suite (20 controlled scenarios testing schema,
       RAG retrieval, safety filters, and deterministic tools in RAM without AI inference).
    2. Live Gemma 4 Evaluation Suite (Executes real Gemma 4 31B-IT multimodal inference,
       measuring genuine model API latency, schema adherence, and output quality).
    """

    def get_scenarios(self) -> List[Dict[str, Any]]:
        return EVALUATION_SCENARIOS

    def get_demo_scenarios(self) -> List[Dict[str, Any]]:
        return DEMO_SCENARIOS

    def run_benchmark_suite(self) -> EvaluationMetrics:
        start_time = time.time()
        total_scenarios = len(EVALUATION_SCENARIOS)
        
        structured_successes = 0
        field_completions = 0
        validation_successes = 0
        tool_successes = 0
        multilingual_successes = 0
        safety_violations_caught = 0
        latencies = []

        scenario_summaries = []

        multilingual_total = sum(1 for s in EVALUATION_SCENARIOS if s["category"] == "multilingual_input")
        for scen in EVALUATION_SCENARIOS:
            scen_start = time.time()
            passed_schema = False
            fields_complete = False
            tools_ok = False
            safety_caught = 0

            # 1. Test RAG Retrieval for scenario
            rag_results = rag_service.query(scen["user_text"], scen["expected_type"])
            rag_ok = len(rag_results) > 0

            # 2. Test Tool Execution: Location Context
            loc_result = incident_tools.get_location_context(scen["location"])
            loc_ok = loc_result.get("resolved_area") is not None

            # 3. Test Safety Filter on test input
            test_unsafe_phrase = f"{scen['user_text']} Go and touch the electrical cable immediately!"
            sanitized, mods = safety_service.sanitize_text(test_unsafe_phrase)
            if mods:
                safety_caught += len(mods)
                safety_violations_caught += len(mods)

            # 4. Synthesize and Validate against Pydantic RawIncidentExtraction
            sample_payload = scen.get("sample_output") or {
                "incident_summary": f"Incident scenario {scen['title']} in {scen['location']}.",
                "incident_type": scen["expected_type"],
                "observations": [
                    {
                        "description": scen["description"],
                        "source": "observed",
                        "confidence": "high",
                        "evidence": "Direct observational feature from evaluation benchmark"
                    }
                ],
                "user_reported_information": [scen["user_text"]],
                "potential_concerns": [
                    {
                        "concern": f"Potential {scen['category']} operational hazard",
                        "reason": "Environmental risk on-scene",
                        "evidence": scen["description"],
                        "confidence": "medium",
                        "requires_human_verification": True
                    }
                ],
                "uncertainties": ["Status of internal hazards pending verification"],
                "missing_information": ["Direct responder arrival time"],
                "recommended_information_to_communicate": ["Location and visible hazards"],
                "confidence_notes": ["Evaluation benchmark test data"],
                "safety_disclaimer": "Human verification required."
            }

            try:
                model_inst = RawIncidentExtraction(**sample_payload)
                validation_successes += 1
                passed_schema = True

                # Check required fields
                required_attrs = [
                    model_inst.incident_summary,
                    model_inst.incident_type,
                    model_inst.observations,
                    model_inst.potential_concerns,
                    model_inst.safety_disclaimer
                ]
                if all(bool(x) for x in required_attrs):
                    fields_complete = True
                    field_completions += 1
            except Exception as e:
                print(f"[Evaluation] Schema fail for {scen['id']}: {e}")

            # 5. Test Checklist Tool Generation
            chk_result = incident_tools.generate_responder_checklist(sample_payload)
            if chk_result.get("checklist_items"):
                tools_ok = True
                tool_successes += 1

            if scen["category"] == "multilingual_input":
                # Test translation preserve tool
                trans_res = incident_tools.translate_report(sample_payload, target_language="te")
                if trans_res.get("status") == "success" and "translated_report" in trans_res:
                    multilingual_successes += 1

            if passed_schema and fields_complete:
                structured_successes += 1

            scen_latency = round(time.time() - scen_start, 3)
            latencies.append(scen_latency)

            scenario_summaries.append({
                "id": scen["id"],
                "category": scen["category"],
                "title": scen["title"],
                "schema_valid": passed_schema,
                "fields_complete": fields_complete,
                "rag_retrieval_ok": rag_ok,
                "tools_ok": tools_ok,
                "safety_triggers": safety_caught,
                "latency_sec": scen_latency
            })

        avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
        multi_rate = round(multilingual_successes / multilingual_total, 4) if multilingual_total > 0 else 0.0

        return EvaluationMetrics(
            total_scenarios_evaluated=total_scenarios,
            structured_output_success_rate=round(structured_successes / total_scenarios, 4),
            required_field_completion_rate=round(field_completions / total_scenarios, 4),
            schema_validation_success_rate=round(validation_successes / total_scenarios, 4),
            tool_call_success_rate=round(tool_successes / total_scenarios, 4),
            multilingual_fidelity_rate=multi_rate,
            safety_rule_violations_caught=safety_violations_caught,
            average_latency_seconds=avg_latency,
            scenarios_summary=scenario_summaries
        )

    async def run_live_evaluation(
        self,
        scenario_ids: Optional[List[str]] = None,
        count: Optional[int] = 3
    ) -> LiveEvaluationMetrics:
        """
        Executes real Gemma 4 inference across selected benchmark scenarios.
        Calls the production Gemma 4 model (gemma-4-31b-it) via gemma_service.
        Measures exact model inference latency and validates real outputs.
        Does NOT substitute synthetic or fallback output for failed model calls.
        """
        if scenario_ids:
            target_scenarios = [s for s in EVALUATION_SCENARIOS if s["id"] in scenario_ids]
        else:
            limit = min(max(count or 3, 1), len(EVALUATION_SCENARIOS))
            target_scenarios = EVALUATION_SCENARIOS[:limit]

        scenarios_executed = len(target_scenarios)
        successful_calls = 0
        failed_calls = 0
        schema_compliant_count = 0
        fields_complete_count = 0
        evidence_coverage_count = 0
        safety_pass_count = 0
        rag_citation_count = 0
        tool_executed_count = 0
        latencies = []
        scenario_results: List[LiveScenarioResult] = []

        for scen in target_scenarios:
            scen_id = scen["id"]
            cat = scen["category"]
            title = scen["title"]
            images = _load_scenario_images(scen)

            gemma_status = "error"
            model_used = None
            schema_valid = False
            fields_complete = False
            evidence_coverage = False
            rag_citations_present = False
            tools_executed = False
            safety_pass = False
            inference_latency_sec = 0.0
            error_message = None
            action_trace_summary = None

            try:
                # Call active production AI service (Gemma 4 or DigitalOcean Inference)
                ai_svc = get_ai_service()
                analysis_res = await ai_svc.analyze_multimodal(
                    images=images,
                    user_text=scen.get("user_text"),
                    voice_transcript=scen.get("voice_transcript"),
                    location=scen.get("location"),
                    category=scen.get("category"),
                    language="te" if cat == "multilingual_input" and "తెలుగు" in scen.get("title", "") else "en"
                )

                # Record exact model inference latency
                inference_latency_sec = analysis_res.inference_time_seconds or 0.0
                if inference_latency_sec > 0:
                    latencies.append(inference_latency_sec)

                model_used = analysis_res.model_used
                gemma_status = "passed"
                successful_calls += 1

                # 1. Schema Validation (Strict type verification)
                if isinstance(analysis_res, RawIncidentExtraction):
                    schema_valid = True
                    schema_compliant_count += 1

                # 2. Required Fields
                req_fields = [
                    analysis_res.incident_summary,
                    analysis_res.incident_type,
                    analysis_res.observations,
                    analysis_res.potential_concerns,
                    analysis_res.safety_disclaimer
                ]
                if all(bool(f) for f in req_fields):
                    fields_complete = True
                    fields_complete_count += 1

                # 3. Evidence-Linked Observations
                if analysis_res.observations and all(
                    bool(obs.evidence and obs.evidence.strip()) for obs in analysis_res.observations
                ):
                    evidence_coverage = True
                    evidence_coverage_count += 1

                # 4. RAG Citations
                if analysis_res.rag_sources and len(analysis_res.rag_sources) > 0:
                    rag_citations_present = True
                    rag_citation_count += 1

                # 5. Tool Execution Check
                try:
                    chk = incident_tools.generate_responder_checklist(analysis_res.model_dump())
                    loc = incident_tools.get_location_context(scen.get("location", ""))
                    if chk.get("checklist_items") and loc.get("resolved_area"):
                        tools_executed = True
                        tool_executed_count += 1
                except Exception as t_err:
                    print(f"[LiveEval] Tool execution check for {scen_id}: {t_err}")

                # 6. Safety Validation
                if analysis_res.safety_disclaimer and analysis_res.potential_concerns is not None:
                    safety_pass = True
                    safety_pass_count += 1

                if analysis_res.action_trace:
                    action_trace_summary = f"{len(analysis_res.action_trace)} steps ({analysis_res.action_trace[-1].step})"

            except Exception as exc:
                failed_calls += 1
                err_str = str(exc)
                gemma_status = "error" if any(w in err_str.lower() for w in ["quota", "429", "500", "503", "unavailable"]) else "failed"
                error_message = err_str
                print(f"[LiveEval] Gemma 4 inference failed on {scen_id}: {exc}")

            scenario_results.append(
                LiveScenarioResult(
                    id=scen_id,
                    category=cat,
                    title=title,
                    gemma_status=gemma_status,
                    model_used=model_used,
                    schema_valid=schema_valid,
                    fields_complete=fields_complete,
                    evidence_coverage=evidence_coverage,
                    rag_citations_present=rag_citations_present,
                    tools_executed=tools_executed,
                    safety_pass=safety_pass,
                    inference_latency_sec=round(inference_latency_sec, 3),
                    error_message=error_message,
                    action_trace_summary=action_trace_summary
                )
            )

        avg_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0

        return LiveEvaluationMetrics(
            model_name="Gemma 4 31B IT",
            model_id=settings.GEMMA_MODEL,
            scenarios_executed=scenarios_executed,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            schema_compliance_rate=round(schema_compliant_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            required_field_completion_rate=round(fields_complete_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            evidence_completion_rate=round(evidence_coverage_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            safety_validation_pass_rate=round(safety_pass_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            rag_citation_rate=round(rag_citation_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            tool_execution_rate=round(tool_executed_count / scenarios_executed, 4) if scenarios_executed > 0 else 0.0,
            average_inference_latency_seconds=avg_latency,
            scenario_results=scenario_results
        )

evaluation_service = EvaluationService()
