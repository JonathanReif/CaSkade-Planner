class SparqlQueries: 
    
    def __init__(self) -> None:
        
        # Get all resource properties for capability effect that has to be updated by output information (Assurance) which is equal (Cap Constraint) to input information (Actual Value) 
        self.sparql_cap_eff_res_prop = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>

            select ?cap ?id_i ?prop where {  
                ?cap a cask:ProvidedCapability;
                    VDI3682:hasOutput ?o; 
                    VDI3682:hasInput ?i.
                ?o a VDI3682:Information; 
                DINEN61360:has_Data_Element ?de.
                ?de DINEN61360:has_Instance_Description ?id;
                    DINEN61360:has_Type_Description ?type.
                ?id DINEN61360:Expression_Goal "Assurance";
                    DINEN61360:Logic_Interpretation "=". 
                ?i a VDI3682:Information; 
                DINEN61360:has_Data_Element ?de_i.
                ?de_i DINEN61360:has_Instance_Description ?id_i;
                    DINEN61360:has_Type_Description ?type.
                ?id_i DINEN61360:Expression_Goal "Actual_Value";
                    DINEN61360:Logic_Interpretation "=". 
                FILTER NOT EXISTS {?cap VDI3682:hasOutput ?op. 
                    ?op a VDI3682:Product.
                    ?id DINEN61360:Value ?value. 	
                } 
                ?res a css:Resource; 
                    css:providesCapability ?cap; 
                    DINEN61360:has_Data_Element ?res_de. 
                ?res_de DINEN61360:has_Instance_Description ?prop;
                        DINEN61360:has_Type_Description ?type. 
                ?prop DINEN61360:Expression_Goal "Actual_Value";
                        DINEN61360:Logic_Interpretation "=". 
            } """

        # Get initial state of resource 
        self.sparql_res_init = """
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
            select ?id ?val where { 
                ?res a css:Resource; 
                    DINEN61360:has_Data_Element ?de. 
                ?de a DINEN61360:Data_Element;
                    DINEN61360:has_Instance_Description ?id. 
                ?id a DINEN61360:Instance_Description; 
                    DINEN61360:Expression_Goal "Actual_Value"; 
                    DINEN61360:Logic_Interpretation "="; 
                    DINEN61360:Value ?val. 
            } """

        '''
        Get goal state of resource 
        When goal of req cap is information with assurance connection to resource has to be made.. 
        '''        
        self.sparql_res_goal = """
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            select ?res_id ?val where { 
                ?res a css:Resource;
                    css:providesCapability ?cap;
                    DINEN61360:has_Data_Element ?res_de. 
                ?res_de a DINEN61360:Data_Element;
                    DINEN61360:has_Instance_Description ?res_id;
                    DINEN61360:has_Type_Description ?type. 
                ?res_id a DINEN61360:Instance_Description; 
                    DINEN61360:Expression_Goal "Actual_Value"; 
                    DINEN61360:Logic_Interpretation "=". 
                ?cap a cask:RequiredCapability;
                    VDI3682:hasOutput ?out. 
                ?out a VDI3682:Information;
                    DINEN61360:has_Data_Element ?de. 
                ?de a DINEN61360:Data_Element;
                    DINEN61360:has_Instance_Description ?id;
                    DINEN61360:has_Type_Description ?type. 
                ?id a DINEN61360:Instance_Description; 
                    DINEN61360:Expression_Goal "Requirement"; 
                    DINEN61360:Logic_Interpretation "="; 
                    DINEN61360:Value ?val. 
            }  """
    
    def get_sparql_cap_eff_res_prop(self):
        return self.sparql_cap_eff_res_prop
    
    def get_sparql_res_init(self): 
        return self.sparql_res_init
    
    def get_sparql_res_goal(self):
        return self.sparql_res_goal