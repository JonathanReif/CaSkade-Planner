class SparqlQueries: 
    
    def __init__(self) -> None:
        
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
    
    def get_sparql_res_init(self): 
        return self.sparql_res_init
    
    def get_sparql_res_goal(self):
        return self.sparql_res_goal