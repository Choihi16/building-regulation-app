import sys
sys.stdout.reconfigure(encoding='utf-8')
import json

from vworld_api import VWorldClient
from moleg_api import MolegClient
from regulation_engine import RegulationEngine
from report_generator import generate_markdown_report

def main():
    print("=== Testing Upgraded Executive Feasibility Workflow ===")
    vworld = VWorldClient()
    moleg = MolegClient()
    engine = RegulationEngine()
    
    addr = "서울시 성북구 길음동 1284"
    site_info = vworld.geocode(addr)
    land_info = vworld.get_land_use_and_restrictions(site_info["x"], site_info["y"])
    ordin_bundle = moleg.get_municipal_ordinance_bundle(site_info["sido"], site_info["sigg"])
    
    analysis = engine.analyze(
        site_info=site_info,
        land_info=land_info,
        ordin_bundle=ordin_bundle,
        site_area=1500.0,
        planned_usage="공동주택 (아파트)",
        unit_count=120,
        unit_area=84.0
    )
    
    feas = analysis["feasibility"]
    print("Feasibility:")
    print(f"  Max Building Area: {feas['max_building_area_sqm']} m2 ({feas['max_building_area_py']} py)")
    print(f"  Ground GFA: {feas['max_ground_gfa_sqm']} m2 ({feas['max_ground_gfa_py']} py)")
    print(f"  Incentive GFA: {feas['incentive_ground_gfa_sqm']} m2 ({feas['incentive_ground_gfa_py']} py)")
    print(f"  Est Floors: {feas['est_floors']}F, Est Height: {feas['est_height_m']}m")
    
    parking = analysis["design_constraints"]["parking"]
    print("Parking:")
    print(f"  Legal: {parking['legal_count']}대, Rec: {parking['recommended_count']}대, EV: {parking['ev_charging_count']}대")
    
    delibs = analysis["deliberations"]
    print("Deliberations:")
    print(f"  Risk Count: {delibs['risk_summary']['high_risk_count']}, Grade: {delibs['risk_summary']['overall_grade']}")
    for it in delibs["items"]:
        print(f"    - {it['name']}: {it['required']} [{it['tag']}] -> {it['timeline']}")
        
    print("\n3-Line Summary:")
    for l in analysis["executive_summary_3lines"]:
        print(" ", l)
        
    md = generate_markdown_report(analysis)
    print(f"\nReport generated ({len(md)} bytes)")
    print("=== Test PASSED Successfully! ===")

if __name__ == "__main__":
    main()
