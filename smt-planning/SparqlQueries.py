class SparqlQueries: 
    
    def __init__(self) -> None:
        
        # Get all properties of resources 
        self.sparql_resource_props = """
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>

            select ?prop where { 
                ?res a css:Resource ; 
                    DINEN61360:has_Data_Element ?de. 
                ?de DINEN61360:has_Instance_Description ?prop.  
            } """

        # Get all capabilities 
        self.sparql_caps = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>

            select ?cap where { 
                ?cap a cask:ProvidedCapability. 
            } """
        
        # Get all capability properties 
        self.sparql_cap_props = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>

            select ?prop where { 
                ?cap a cask:ProvidedCapability;
                    VDI3682:hasInput | VDI3682:hasOutput ?io. 
                ?io DINEN61360:has_Data_Element ?de.
                ?de DINEN61360:has_Instance_Description ?prop.
    			?prop DINEN61360:Expression_Goal ?expr. 

  				FILTER NOT EXISTS {
    				?io a VDI3682:Information.
    				FILTER (
      					?expr = "Assurance" || ?expr = "Requirement"
 					)
  				}
            } """

        # Get all capability properties of outputs (when output is product)
        self.sparql_cap_out_props = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>

            select ?cap ?prop where { 
                ?cap a cask:ProvidedCapability;
                    VDI3682:hasOutput ?out. 
                ?out a VDI3682:Product;
                    DINEN61360:has_Data_Element ?de.
                ?de DINEN61360:has_Instance_Description ?prop. 
            } """  

        # Get all resource properties that are influenced by capability effect. Check for Capability Constraints 
        # self.sparql_res_prop_cap_eff_old = """
        #     PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
        #     PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
        #     PREFIX css: <http://www.w3id.org/hsu-aut/css#>
        #     PREFIX m: <http://openmath.org/vocab/math#>

        #     select ?cap ?prop where { 
        #         ?res a css:Resource ; 
        #             DINEN61360:has_Data_Element ?de.
        #         ?de DINEN61360:has_Instance_Description ?prop.
        #         ?prop ^css:references ?cap_const. 
        #         ?cap_const a m:Application; 
        #             ^css:isRestrictedBy ?cap. 
        #         ?cap a cask:ProvidedCapability.                 
        #     } """

        '''
        Get all resource properties that are influenced by capability effect
        capability has information output with assurance = (no value) 
        capability has information input with actual_value = (no value)
        input and output information connected with cap constraint 
        capability has no product output, then it has to reference to resoruce 
        '''
        self.sparql_res_prop_cap_eff = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>
            PREFIX m: <http://openmath.org/vocab/math#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            select ?cap ?prop where { 
                ?res a css:Resource ; 
                    DINEN61360:has_Data_Element ?de;
                    css:providesCapability ?cap. 
                ?de a DINEN61360:Data_Element;
                    DINEN61360:has_Instance_Description ?prop;
                    DINEN61360:has_Type_Description ?type. 
                ?prop a DINEN61360:Instance_Description. 
                ?cap a cask:ProvidedCapability;  
                    VDI3682:hasOutput ?out_inf;
                    VDI3682:hasInput ?in_inf; 
                    css:isRestrictedBy ?constr. 
                ?out_inf a VDI3682:Information; 
                    DINEN61360:has_Data_Element ?out_inf_de. 
                ?out_inf_de a DINEN61360:Data_Element; 
                    DINEN61360:has_Instance_Description ?out_inf_id;
                    DINEN61360:has_Type_Description ?type. 
                ?out_inf_id a DINEN61360:Instance_Description; 
                    DINEN61360:Expression_Goal "Assurance"; 
                    DINEN61360:Logic_Interpretation	"=".
                ?in_inf a VDI3682:Information; 
                    DINEN61360:has_Data_Element ?in_inf_de. 
                ?in_inf_de a DINEN61360:Data_Element;  
                    DINEN61360:has_Instance_Description ?in_inf_id;
                    DINEN61360:has_Type_Description ?type.
                ?in_inf_id a DINEN61360:Instance_Description;            
                    DINEN61360:Expression_Goal "Actual_Value"; 
                    DINEN61360:Logic_Interpretation	"=".
                ?constr a m:Application; 
                    m:operator m:eq; 
                    css:references ?in_inf_id; 
                    css:references ?out_inf_id. 
                    
                FILTER NOT EXISTS {?out_inf_id DINEN61360:Value ?out_val.
                    ?in_inf_id DINEN61360:Value ?in_val. 
                    ?cap VDI3682:hasOutput ?op. 
                    ?op a VDI3682:Product. }
            } """
        
        # Get all resource properties for capability precondition that has to be compared with input information property (Requirement). 
        self.sparql_cap_pre_res_prop = """
            PREFIX cask: <http://www.w3id.org/hsu-aut/cask#>
            PREFIX VDI3682: <http://www.hsu-ifa.de/ontologies/VDI3682#>
            PREFIX DINEN61360: <http://www.hsu-ifa.de/ontologies/DINEN61360#>
            PREFIX css: <http://www.w3id.org/hsu-aut/css#>

            select ?cap ?log ?val ?res_id where {  
                ?cap a cask:ProvidedCapability;
                    VDI3682:hasInput ?i. 
                ?i a VDI3682:Information; 
                DINEN61360:has_Data_Element ?de.
                ?de DINEN61360:has_Instance_Description ?id;
                    DINEN61360:has_Type_Description ?type.
                ?id DINEN61360:Expression_Goal "Requirement";
                    DINEN61360:Logic_Interpretation ?log;
                    DINEN61360:Value ?val.
                FILTER NOT EXISTS {?cap VDI3682:hasInput ?ip. 
                    ?ip a VDI3682:Product.} 
                ?res a css:Resource; 
                    css:providesCapability ?cap; 
                    DINEN61360:has_Data_Element ?res_de. 
                ?res_de DINEN61360:has_Instance_Description ?res_id;
                        DINEN61360:has_Type_Description ?type. 
                ?res_id DINEN61360:Expression_Goal "Actual_Value";
                        DINEN61360:Logic_Interpretation "=". 
            } """
        
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


    def get_sparql_resource_props(self):
        return self.sparql_resource_props
    
    def get_sparql_caps(self):
        return self.sparql_caps
    
    def get_sparql_cap_props(self):
        return self.sparql_cap_props
    
    def get_sparql_cap_out_props(self):
        return self.sparql_cap_out_props
    
    def get_sparql_res_prop_cap_eff(self):
        return self.sparql_res_prop_cap_eff
    
    def get_sparql_cap_pre_res_prop(self):
        return self.sparql_cap_pre_res_prop
    
    def get_sparql_cap_eff_res_prop(self):
        return self.sparql_cap_eff_res_prop
    
    def get_sparql_res_init(self): 
        return self.sparql_res_init
    
    def get_sparql_res_goal(self):
        return self.sparql_res_goal