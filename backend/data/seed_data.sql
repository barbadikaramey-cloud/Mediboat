BEGIN TRANSACTION;
CREATE TABLE claims (
            claim_id        TEXT PRIMARY KEY,
            patient_id      TEXT,
            patient_name    TEXT,
            department      TEXT,
            claim_type      TEXT,
            diagnosis_code  TEXT,
            insurer         TEXT,
            claimed_amount  REAL,
            approved_amount REAL,
            status          TEXT,
            submitted_date  TEXT,
            resolved_date   TEXT
        );
INSERT INTO "claims" VALUES('CLM-2024-1000','PAT-51347','Kavya Pillai','nephrology','reimbursement','N17.9','New India Assurance',72700.0,NULL,'pending','2024-01-26',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1001','PAT-75435','Kavya Das','cardiology','cashless','I21.4','Bajaj Allianz',129900.0,NULL,'pending','2024-04-21',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1002','PAT-57447','Pari Naidu','neurology','cashless','I63.9','United India',91000.0,83200.0,'approved','2024-12-19','2024-12-28');
INSERT INTO "claims" VALUES('CLM-2024-1003','PAT-88172','Arjun Shetty','gynaecology','cashless','O82','HDFC Ergo',47700.0,41700.0,'approved','2024-03-21','2024-04-06');
INSERT INTO "claims" VALUES('CLM-2024-1004','PAT-99353','Manoj Mehta','orthopaedics','cashless','M17.0','Star Health',192400.0,NULL,'rejected','2024-11-24','2024-12-02');
INSERT INTO "claims" VALUES('CLM-2024-1005','PAT-44522','Anil Mehta','general_medicine','cashless','E11.9','Care Health',7800.0,NULL,'pending','2024-01-24',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1006','PAT-89818','Aadhya Naidu','general_medicine','reimbursement','D64.9','United India',9700.0,NULL,'submitted','2024-11-17',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1007','PAT-57576','Riya Menon','orthopaedics','reimbursement','S72.0','Star Health',211700.0,195500.0,'approved','2024-10-11','2024-10-17');
INSERT INTO "claims" VALUES('CLM-2024-1008','PAT-19071','Manoj Mehta','cardiology','reimbursement','I21.4','HDFC Ergo',129100.0,NULL,'pending','2024-12-16',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1009','PAT-37760','Manoj Mehta','cardiology','reimbursement','I21.4','ICICI Lombard',123800.0,121400.0,'approved','2024-05-17','2024-06-02');
INSERT INTO "claims" VALUES('CLM-2024-1010','PAT-69177','Krishna Menon','orthopaedics','cashless','S72.0','Bajaj Allianz',212100.0,NULL,'escalated','2024-08-17',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1011','PAT-10942','Arjun Subramaniam','general_medicine','cashless','J44.1','New India Assurance',40600.0,NULL,'pending','2024-10-08',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1012','PAT-38080','Manoj Naidu','neurology','reimbursement','G40.9','Bajaj Allianz',30300.0,26800.0,'approved','2024-02-17','2024-03-06');
INSERT INTO "claims" VALUES('CLM-2024-1013','PAT-22363','Reyansh Krishnan','nephrology','cashless','E11.2','Care Health',55800.0,NULL,'pending','2024-07-07',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1014','PAT-17944','Kavya Chowdary','orthopaedics','cashless','S52.5','Star Health',37400.0,37300.0,'approved','2024-11-21','2024-11-27');
INSERT INTO "claims" VALUES('CLM-2024-1015','PAT-42742','Arjun Desai','general_medicine','cashless','J44.1','Care Health',39900.0,35000.0,'approved','2024-03-14','2024-03-31');
INSERT INTO "claims" VALUES('CLM-2024-1016','PAT-73653','Ramesh Nair','orthopaedics','reimbursement','M17.0','New India Assurance',188200.0,NULL,'escalated','2024-03-14',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1017','PAT-65444','Prakash Krishnan','orthopaedics','cashless','S72.0','Niva Bupa',195900.0,189600.0,'approved','2024-05-26','2024-06-07');
INSERT INTO "claims" VALUES('CLM-2024-1018','PAT-17492','Vihaan Bhat','nephrology','cashless','N17.9','Star Health',63300.0,59000.0,'approved','2024-10-24','2024-11-06');
INSERT INTO "claims" VALUES('CLM-2024-1019','PAT-62923','Krishna Das','gynaecology','cashless','O80','ICICI Lombard',25500.0,21900.0,'approved','2024-02-20','2024-03-01');
INSERT INTO "claims" VALUES('CLM-2024-1020','PAT-86503','Venkat Kulkarni','gynaecology','cashless','O80','HDFC Ergo',28400.0,NULL,'pending','2024-07-22',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1021','PAT-69929','Lakshmi Bose','general_medicine','reimbursement','A09','New India Assurance',20700.0,18000.0,'approved','2024-05-13','2024-05-25');
INSERT INTO "claims" VALUES('CLM-2024-1022','PAT-37938','Anil Pillai','emergency','cashless','K35.2','HDFC Ergo',58600.0,NULL,'pending','2024-02-18',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1023','PAT-81200','Riya Acharya','cardiology','reimbursement','I50.0','Bajaj Allianz',102200.0,NULL,'rejected','2024-05-06','2024-05-25');
INSERT INTO "claims" VALUES('CLM-2024-1024','PAT-44664','Krishna Das','neurology','reimbursement','G45.9','United India',36100.0,35800.0,'approved','2024-11-04','2024-11-11');
INSERT INTO "claims" VALUES('CLM-2024-1025','PAT-44600','Anil Joshi','cardiology','cashless','I21.4','Bajaj Allianz',114500.0,NULL,'rejected','2024-04-22','2024-05-17');
INSERT INTO "claims" VALUES('CLM-2024-1026','PAT-31178','Rajesh Deshpande','general_medicine','cashless','J18.9','United India',41300.0,39900.0,'approved','2024-01-11','2024-01-22');
INSERT INTO "claims" VALUES('CLM-2024-1027','PAT-29410','Nisha Naidu','nephrology','cashless','N17.9','ICICI Lombard',68800.0,67100.0,'approved','2024-09-02','2024-09-22');
INSERT INTO "claims" VALUES('CLM-2024-1028','PAT-56357','Prakash Das','cardiology','reimbursement','I50.0','Star Health',92400.0,88000.0,'approved','2024-06-07','2024-06-13');
INSERT INTO "claims" VALUES('CLM-2024-1029','PAT-64040','Vivaan Iyer','orthopaedics','reimbursement','M17.0','New India Assurance',183700.0,NULL,'rejected','2024-03-26','2024-04-05');
INSERT INTO "claims" VALUES('CLM-2024-1030','PAT-60140','Aditya Mukherjee','emergency','cashless','K80.2','New India Assurance',61300.0,59300.0,'approved','2024-05-06','2024-05-12');
INSERT INTO "claims" VALUES('CLM-2024-1031','PAT-39219','Vivaan Krishnan','gynaecology','reimbursement','O80','Bajaj Allianz',26300.0,25500.0,'approved','2024-05-27','2024-06-06');
INSERT INTO "claims" VALUES('CLM-2024-1032','PAT-53404','Vivaan Rao','general_medicine','reimbursement','R50.9','United India',14500.0,13400.0,'approved','2024-06-21','2024-07-11');
INSERT INTO "claims" VALUES('CLM-2024-1033','PAT-55309','Lakshmi Hegde','general_medicine','reimbursement','J45.9','Star Health',18300.0,NULL,'rejected','2024-02-20','2024-03-09');
INSERT INTO "claims" VALUES('CLM-2024-1034','PAT-80575','Aadhya Patel','orthopaedics','cashless','M17.0','Niva Bupa',171200.0,NULL,'escalated','2024-01-17',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1035','PAT-76469','Riya Krishnan','orthopaedics','reimbursement','S72.0','Bajaj Allianz',228900.0,198800.0,'approved','2024-11-28','2024-12-10');
INSERT INTO "claims" VALUES('CLM-2024-1036','PAT-98777','Diya Acharya','orthopaedics','cashless','S52.5','ICICI Lombard',37300.0,35400.0,'approved','2024-04-14','2024-04-29');
INSERT INTO "claims" VALUES('CLM-2024-1037','PAT-67954','Saanvi Kulkarni','cardiology','cashless','I21.0','Bajaj Allianz',184200.0,NULL,'escalated','2024-08-15',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1038','PAT-98184','Riya Menon','gynaecology','cashless','O80','Bajaj Allianz',28900.0,28700.0,'approved','2024-02-27','2024-03-08');
INSERT INTO "claims" VALUES('CLM-2024-1039','PAT-64321','Venkat Nair','general_medicine','cashless','J45.9','Care Health',16300.0,15700.0,'approved','2024-10-28','2024-11-14');
INSERT INTO "claims" VALUES('CLM-2024-1040','PAT-65724','Pari Iyer','nephrology','cashless','E11.2','ICICI Lombard',53700.0,45700.0,'approved','2024-11-23','2024-11-29');
INSERT INTO "claims" VALUES('CLM-2024-1041','PAT-97500','Sunil Deshpande','nephrology','cashless','E11.2','HDFC Ergo',54600.0,NULL,'rejected','2024-08-05','2024-08-24');
INSERT INTO "claims" VALUES('CLM-2024-1042','PAT-68991','Navya Mehta','neurology','reimbursement','I63.9','Niva Bupa',106800.0,105200.0,'approved','2024-09-15','2024-10-03');
INSERT INTO "claims" VALUES('CLM-2024-1043','PAT-47450','Anika Pillai','general_medicine','cashless','A09','New India Assurance',23200.0,NULL,'rejected','2024-05-15','2024-05-22');
INSERT INTO "claims" VALUES('CLM-2024-1044','PAT-18418','Meera Hegde','general_medicine','cashless','E11.9','ICICI Lombard',9200.0,8800.0,'approved','2024-04-13','2024-04-22');
INSERT INTO "claims" VALUES('CLM-2024-1045','PAT-85456','Deepa Joshi','general_medicine','cashless','D64.9','Niva Bupa',8900.0,8300.0,'approved','2024-07-25','2024-07-28');
INSERT INTO "claims" VALUES('CLM-2024-1046','PAT-73993','Pari Pillai','cardiology','cashless','I50.0','Niva Bupa',91200.0,87600.0,'approved','2024-09-24','2024-10-04');
INSERT INTO "claims" VALUES('CLM-2024-1047','PAT-26728','Harish Deshpande','orthopaedics','cashless','S52.5','Niva Bupa',34400.0,NULL,'rejected','2024-12-06','2024-12-25');
INSERT INTO "claims" VALUES('CLM-2024-1048','PAT-27786','Suresh Iyer','cardiology','cashless','I48.0','HDFC Ergo',38700.0,NULL,'pending','2024-11-14',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1049','PAT-65255','Navya Banerjee','cardiology','cashless','I21.0','Niva Bupa',188400.0,NULL,'escalated','2024-05-25',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1050','PAT-14067','Anika Nair','cardiology','cashless','I48.0','Bajaj Allianz',34300.0,29500.0,'approved','2024-04-21','2024-04-25');
INSERT INTO "claims" VALUES('CLM-2024-1051','PAT-70952','Navya Mehta','cardiology','cashless','I21.4','HDFC Ergo',113700.0,NULL,'pending','2024-10-07',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1052','PAT-50888','Venkat Krishnan','orthopaedics','reimbursement','S72.0','HDFC Ergo',214400.0,185700.0,'approved','2024-03-10','2024-03-13');
INSERT INTO "claims" VALUES('CLM-2024-1053','PAT-49529','Naveen Agarwal','orthopaedics','cashless','S52.5','New India Assurance',41400.0,NULL,'pending','2024-02-23',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1054','PAT-54725','Aarav Mukherjee','cardiology','cashless','I21.0','Bajaj Allianz',179300.0,NULL,'rejected','2024-02-17','2024-03-13');
INSERT INTO "claims" VALUES('CLM-2024-1055','PAT-95256','Myra Acharya','orthopaedics','reimbursement','S52.5','Care Health',35000.0,32000.0,'approved','2024-12-05','2024-12-24');
INSERT INTO "claims" VALUES('CLM-2024-1056','PAT-42177','Sai Pillai','gynaecology','reimbursement','O82','United India',51600.0,NULL,'pending','2024-06-28',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1057','PAT-52600','Diya Joshi','orthopaedics','cashless','S72.0','Niva Bupa',220500.0,NULL,'rejected','2024-06-01','2024-06-21');
INSERT INTO "claims" VALUES('CLM-2024-1058','PAT-21221','Anika Chowdary','general_medicine','cashless','E11.9','United India',9000.0,8300.0,'approved','2024-09-01','2024-09-10');
INSERT INTO "claims" VALUES('CLM-2024-1059','PAT-74332','Rajesh Agarwal','orthopaedics','cashless','S52.5','Care Health',38400.0,NULL,'pending','2024-11-23',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1060','PAT-58368','Ramesh Deshpande','cardiology','cashless','I21.0','New India Assurance',177400.0,NULL,'rejected','2024-05-22','2024-06-14');
INSERT INTO "claims" VALUES('CLM-2024-1061','PAT-42951','Pari Rao','orthopaedics','cashless','M17.0','Care Health',180700.0,NULL,'escalated','2024-05-10',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1062','PAT-87278','Sunil Acharya','nephrology','reimbursement','N18.3','ICICI Lombard',4000.0,3800.0,'approved','2024-04-07','2024-04-18');
INSERT INTO "claims" VALUES('CLM-2024-1063','PAT-11854','Manoj Naidu','general_medicine','cashless','J44.1','Bajaj Allianz',44800.0,NULL,'pending','2024-03-10',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1064','PAT-74340','Reyansh Mukherjee','general_medicine','cashless','J18.9','ICICI Lombard',49300.0,NULL,'submitted','2024-08-25',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1065','PAT-24953','Arjun Shetty','cardiology','cashless','I50.0','ICICI Lombard',94400.0,NULL,'rejected','2024-01-09','2024-01-29');
INSERT INTO "claims" VALUES('CLM-2024-1066','PAT-21164','Anika Rao','gynaecology','cashless','O80','ICICI Lombard',28400.0,26500.0,'approved','2024-03-26','2024-04-07');
INSERT INTO "claims" VALUES('CLM-2024-1067','PAT-87139','Nisha Gupta','orthopaedics','cashless','M17.0','Care Health',172200.0,NULL,'escalated','2024-08-10',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1068','PAT-44687','Sai Iyer','gynaecology','reimbursement','O80','New India Assurance',28600.0,NULL,'pending','2024-11-07',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1069','PAT-14278','Pari Gupta','general_medicine','cashless','J45.9','Niva Bupa',18200.0,17100.0,'approved','2024-08-23','2024-09-04');
INSERT INTO "claims" VALUES('CLM-2024-1070','PAT-65723','Krishna Deshpande','nephrology','cashless','N17.9','New India Assurance',70800.0,68600.0,'approved','2024-05-26','2024-06-04');
INSERT INTO "claims" VALUES('CLM-2024-1071','PAT-84607','Kiara Desai','cardiology','cashless','I21.0','United India',177700.0,NULL,'escalated','2024-10-24',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1072','PAT-74722','Rajesh Reddy','cardiology','cashless','I48.0','United India',39400.0,NULL,'submitted','2024-09-18',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1073','PAT-98117','Myra Bhat','neurology','reimbursement','G40.9','United India',34500.0,30500.0,'approved','2024-01-03','2024-01-06');
INSERT INTO "claims" VALUES('CLM-2024-1074','PAT-67132','Vijay Reddy','cardiology','cashless','I21.4','United India',119300.0,NULL,'pending','2024-03-19',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1075','PAT-47777','Kavya Banerjee','gynaecology','cashless','O82','HDFC Ergo',51000.0,46500.0,'approved','2024-03-11','2024-03-29');
INSERT INTO "claims" VALUES('CLM-2024-1076','PAT-62976','Anil Banerjee','emergency','cashless','K40.9','United India',43600.0,NULL,'pending','2024-06-04',NULL);
INSERT INTO "claims" VALUES('CLM-2024-1077','PAT-16764','Saanvi Pillai','cardiology','cashless','I48.0','Bajaj Allianz',37300.0,34500.0,'approved','2024-10-25','2024-11-11');
INSERT INTO "claims" VALUES('CLM-2024-1078','PAT-30758','Riya Deshpande','gynaecology','cashless','O80','Care Health',30400.0,30300.0,'approved','2024-02-01','2024-02-11');
INSERT INTO "claims" VALUES('CLM-2024-1079','PAT-75323','Kiara Kulkarni','cardiology','reimbursement','I48.0','HDFC Ergo',34900.0,33100.0,'approved','2024-08-04','2024-08-11');
INSERT INTO "claims" VALUES('CLM-2024-1080','PAT-34983','Naveen Kulkarni','nephrology','cashless','N17.9','Care Health',66900.0,62400.0,'approved','2024-04-15','2024-04-30');
INSERT INTO "claims" VALUES('CLM-2024-1081','PAT-47072','Riya Banerjee','emergency','cashless','K35.2','Niva Bupa',69700.0,64600.0,'approved','2024-06-26','2024-06-29');
INSERT INTO "claims" VALUES('CLM-2024-1082','PAT-82340','Manoj Shetty','neurology','cashless','G45.9','ICICI Lombard',44000.0,40600.0,'approved','2024-08-18','2024-08-31');
INSERT INTO "claims" VALUES('CLM-2024-1083','PAT-15720','Lakshmi Chowdary','orthopaedics','reimbursement','S52.5','New India Assurance',40800.0,36100.0,'approved','2024-10-13','2024-10-29');
INSERT INTO "claims" VALUES('CLM-2024-1084','PAT-26547','Anil Bhat','gynaecology','cashless','O82','ICICI Lombard',50800.0,NULL,'submitted','2024-08-02',NULL);
CREATE TABLE maintenance_tickets (
            ticket_id       TEXT PRIMARY KEY,
            equipment_name  TEXT,
            equipment_id    TEXT,
            category        TEXT,
            campus          TEXT,
            issue_type      TEXT,
            fault_code      TEXT,
            raised_by       TEXT,
            raised_date     TEXT,
            resolved_date   TEXT,
            status          TEXT,
            resolution_note TEXT
        );
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2000','SterilPro 3000','EQ-HC-3588','sterilisation','MediAssist Hyderabad Central','preventive_maintenance',NULL,'Arjun Desai','2024-11-18',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2001','DriveFlow IP-200','EQ-HC-8484','infusion','MediAssist Hyderabad Central','sensor_failure','F-05','Riya Nair','2024-11-14','2024-11-26','resolved','Firmware/drug library updated, verified');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2002','DriveFlow IP-200','EQ-HC-5847','infusion','MediAssist Hyderabad Central','battery_replacement','F-01','Kiara Sharma','2024-04-13','2024-04-23','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2003','RadiPro MX-150','EQ-BOC-1803','radiology','MediAssist Bengaluru Onco Centre','sensor_failure','F-09','Naveen Chowdary','2024-01-19',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2004','SterilPro 3000','EQ-BOC-4588','sterilisation','MediAssist Bengaluru Onco Centre','preventive_maintenance',NULL,'Aadhya Acharya','2024-04-20','2024-05-03','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2005','DriveFlow IP-200','EQ-BOC-8222','infusion','MediAssist Bengaluru Onco Centre','fault_reported','F-01','Aditya Bhat','2024-11-21','2024-11-22','resolved','Firmware/drug library updated, verified');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2006','DriveFlow IP-200','EQ-PS-3877','infusion','MediAssist Pune Speciality','fault_reported','F-01','Aadhya Naidu','2024-05-11','2024-05-23','resolved','Calibration completed, certificate filed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2007','SterilPro 3000','EQ-PS-5210','sterilisation','MediAssist Pune Speciality','preventive_maintenance',NULL,'Ramesh Agarwal','2024-09-17','2024-09-22','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2008','DriveFlow IP-200','EQ-PS-2233','infusion','MediAssist Pune Speciality','preventive_maintenance',NULL,'Rohan Mehta','2024-02-15',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2009','BM-500 Monitor','EQ-S-1228','monitoring','MediAssist Secunderabad','battery_replacement','E-12','Navya Deshpande','2024-06-03','2024-06-16','resolved','Calibration completed, certificate filed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2010','BM-500 Monitor','EQ-S-5295','monitoring','MediAssist Secunderabad','sensor_failure','E-12','Karthik Shetty','2024-11-24',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2011','RadiPro MX-150','EQ-S-4830','radiology','MediAssist Secunderabad','preventive_maintenance',NULL,'Ramesh Sharma','2024-02-22',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2012','RadiPro MX-150','EQ-MCH-2035','radiology','MediAssist Mysuru Clinic Hub','sensor_failure','F-05','Suresh Bose','2024-10-08',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2013','ElectroCautery EC-90','EQ-MCH-1742','surgical','MediAssist Mysuru Clinic Hub','preventive_maintenance',NULL,'Aditya Gupta','2024-11-14','2024-11-16','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2014','SterilPro 3000','EQ-MCH-3222','sterilisation','MediAssist Mysuru Clinic Hub','calibration_due','E-01','Deepa Desai','2024-02-18',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2015','DriveFlow IP-200','EQ-MCH-3531','infusion','MediAssist Mysuru Clinic Hub','battery_replacement','F-12','Meera Murthy','2024-12-24',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2016','BM-500 Monitor','EQ-S-4559','monitoring','MediAssist Secunderabad','sensor_failure','E-07','Rajesh Desai','2024-05-02','2024-05-14','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2017','DriveFlow IP-200','EQ-PS-9920','infusion','MediAssist Pune Speciality','calibration_due',NULL,'Sneha Verma','2024-12-12',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2018','DriveFlow IP-200','EQ-PS-4475','infusion','MediAssist Pune Speciality','fault_reported','F-01','Naveen Sharma','2024-08-03',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2019','BM-500 Monitor','EQ-PS-4538','monitoring','MediAssist Pune Speciality','fault_reported','E-02','Pari Kumar','2024-10-07','2024-10-09','resolved','Cleaned and functional check passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2020','HemaCount HC-20','EQ-BOC-9850','laboratory','MediAssist Bengaluru Onco Centre','sensor_failure','L-03','Navya Agarwal','2024-05-28','2024-05-31','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2021','BM-500 Monitor','EQ-HC-6304','monitoring','MediAssist Hyderabad Central','calibration_due',NULL,'Vivaan Iyer','2024-01-12','2024-01-25','resolved','Cleaned and functional check passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2022','DriveFlow IP-200','EQ-HC-8802','infusion','MediAssist Hyderabad Central','fault_reported','F-08','Rajesh Mehta','2024-09-04','2024-09-16','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2023','DriveFlow IP-200','EQ-MCH-9543','infusion','MediAssist Mysuru Clinic Hub','sensor_failure','F-01','Riya Desai','2024-08-17','2024-08-21','resolved','Battery replaced, unit returned to service');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2024','RadiPro MX-150','EQ-HC-7580','radiology','MediAssist Hyderabad Central','calibration_due',NULL,'Nisha Krishnan','2024-12-28',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2025','BM-500 Monitor','EQ-S-2076','monitoring','MediAssist Secunderabad','battery_replacement','E-01','Ishaan Pillai','2024-02-11','2024-02-21','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2026','RadiPro MX-150','EQ-MCH-9692','radiology','MediAssist Mysuru Clinic Hub','sensor_failure','F-09','Kiara Desai','2024-06-13',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2027','SterilPro 3000','EQ-MCH-8046','sterilisation','MediAssist Mysuru Clinic Hub','battery_replacement','E-01','Rajesh Das','2024-12-04','2024-12-18','resolved','Cleaned and functional check passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2028','BM-500 Monitor','EQ-S-2557','monitoring','MediAssist Secunderabad','sensor_failure','E-12','Lakshmi Hegde','2024-07-14',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2029','DriveFlow IP-200','EQ-PS-2494','infusion','MediAssist Pune Speciality','preventive_maintenance',NULL,'Sai Reddy','2024-03-22','2024-03-30','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2030','SterilPro 3000','EQ-HC-3002','sterilisation','MediAssist Hyderabad Central','preventive_maintenance',NULL,'Meera Patel','2024-03-18','2024-03-19','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2031','ElectroCautery EC-90','EQ-S-6119','surgical','MediAssist Secunderabad','calibration_due',NULL,'Sneha Rao','2024-12-20',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2032','RadiPro MX-150','EQ-MCH-6736','radiology','MediAssist Mysuru Clinic Hub','fault_reported','F-02','Prakash Patel','2024-11-16','2024-11-20','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2033','BM-500 Monitor','EQ-PS-5381','monitoring','MediAssist Pune Speciality','sensor_failure','E-02','Vivaan Iyer','2024-07-28','2024-08-06','resolved','Battery replaced, unit returned to service');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2034','DriveFlow IP-200','EQ-PS-7566','infusion','MediAssist Pune Speciality','preventive_maintenance',NULL,'Arjun Naidu','2024-06-01','2024-06-04','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2035','ElectroCautery EC-90','EQ-HC-8432','surgical','MediAssist Hyderabad Central','calibration_due',NULL,'Priya Iyer','2024-07-07','2024-07-14','resolved','Calibration completed, certificate filed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2036','DriveFlow IP-200','EQ-PS-3549','infusion','MediAssist Pune Speciality','preventive_maintenance',NULL,'Ananya Mehta','2024-10-20','2024-10-22','resolved','Battery replaced, unit returned to service');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2037','RadiPro MX-150','EQ-HC-7947','radiology','MediAssist Hyderabad Central','calibration_due',NULL,'Vijay Acharya','2024-02-22',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2038','SterilPro 3000','EQ-S-6655','sterilisation','MediAssist Secunderabad','preventive_maintenance',NULL,'Nisha Rao','2024-04-25','2024-05-04','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2039','DriveFlow IP-200','EQ-MCH-7475','infusion','MediAssist Mysuru Clinic Hub','sensor_failure','F-12','Naveen Verma','2024-01-08',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2040','BM-500 Monitor','EQ-BOC-3248','monitoring','MediAssist Bengaluru Onco Centre','preventive_maintenance',NULL,'Navya Gupta','2024-04-25',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2041','DriveFlow IP-200','EQ-HC-7229','infusion','MediAssist Hyderabad Central','calibration_due',NULL,'Manoj Subramaniam','2024-04-14','2024-04-17','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2042','BM-500 Monitor','EQ-MCH-8147','monitoring','MediAssist Mysuru Clinic Hub','sensor_failure','E-03','Vivaan Desai','2024-02-13','2024-02-27','resolved','Battery replaced, unit returned to service');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2043','BM-500 Monitor','EQ-PS-7843','monitoring','MediAssist Pune Speciality','sensor_failure','E-07','Kiara Rao','2024-10-13',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2044','DriveFlow IP-200','EQ-HC-6928','infusion','MediAssist Hyderabad Central','preventive_maintenance',NULL,'Sai Hegde','2024-03-26','2024-04-05','resolved','Cable harness reseated, fault cleared');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2045','BM-500 Monitor','EQ-BOC-2288','monitoring','MediAssist Bengaluru Onco Centre','battery_replacement','E-12','Kavya Mukherjee','2024-07-17',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2046','DriveFlow IP-200','EQ-PS-9693','infusion','MediAssist Pune Speciality','fault_reported','F-05','Anil Nair','2024-03-03','2024-03-12','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2047','HemaCount HC-20','EQ-PS-3419','laboratory','MediAssist Pune Speciality','preventive_maintenance',NULL,'Anika Rao','2024-12-27',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2048','BM-500 Monitor','EQ-PS-3902','monitoring','MediAssist Pune Speciality','fault_reported','E-02','Vijay Desai','2024-10-05','2024-10-18','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2049','HemaCount HC-20','EQ-MCH-6179','laboratory','MediAssist Mysuru Clinic Hub','sensor_failure','L-06','Rohan Desai','2024-11-19','2024-11-30','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2050','BM-500 Monitor','EQ-S-9312','monitoring','MediAssist Secunderabad','battery_replacement','E-03','Arjun Gupta','2024-05-19','2024-05-20','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2051','SterilPro 3000','EQ-S-2479','sterilisation','MediAssist Secunderabad','calibration_due',NULL,'Harish Acharya','2024-01-27','2024-02-01','resolved','Sensor recalibrated, within tolerance');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2052','SterilPro 3000','EQ-S-4084','sterilisation','MediAssist Secunderabad','battery_replacement','E-01','Lakshmi Acharya','2024-08-26',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2053','SterilPro 3000','EQ-MCH-6626','sterilisation','MediAssist Mysuru Clinic Hub','fault_reported','E-01','Sai Kulkarni','2024-08-04',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2054','RadiPro MX-150','EQ-BOC-8199','radiology','MediAssist Bengaluru Onco Centre','calibration_due',NULL,'Sunil Kulkarni','2024-02-15',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2055','RadiPro MX-150','EQ-BOC-6543','radiology','MediAssist Bengaluru Onco Centre','preventive_maintenance',NULL,'Naveen Verma','2024-06-10','2024-06-17','resolved','Calibration completed, certificate filed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2056','RadiPro MX-150','EQ-PS-7333','radiology','MediAssist Pune Speciality','calibration_due',NULL,'Kiara Pillai','2024-02-18',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2057','ElectroCautery EC-90','EQ-MCH-6731','surgical','MediAssist Mysuru Clinic Hub','fault_reported','S-05','Riya Murthy','2024-02-19','2024-03-01','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2058','ElectroCautery EC-90','EQ-S-7171','surgical','MediAssist Secunderabad','fault_reported','S-02','Priya Banerjee','2024-05-18',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2059','BM-500 Monitor','EQ-MCH-1298','monitoring','MediAssist Mysuru Clinic Hub','calibration_due',NULL,'Pooja Gupta','2024-06-14','2024-06-23','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2060','BM-500 Monitor','EQ-BOC-3538','monitoring','MediAssist Bengaluru Onco Centre','preventive_maintenance',NULL,'Arjun Gupta','2024-08-07','2024-08-11','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2061','BM-500 Monitor','EQ-MCH-7172','monitoring','MediAssist Mysuru Clinic Hub','sensor_failure','E-12','Rohan Iyer','2024-01-22','2024-01-28','resolved','Faulty board replaced by OEM engineer');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2062','BM-500 Monitor','EQ-MCH-6968','monitoring','MediAssist Mysuru Clinic Hub','fault_reported','E-07','Anika Desai','2024-01-14',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2063','RadiPro MX-150','EQ-PS-6070','radiology','MediAssist Pune Speciality','battery_replacement','F-02','Ramesh Das','2024-09-08',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2064','BM-500 Monitor','EQ-PS-9239','monitoring','MediAssist Pune Speciality','sensor_failure','E-07','Sunil Hegde','2024-08-25','2024-08-30','resolved','Calibration completed, certificate filed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2065','BM-500 Monitor','EQ-BOC-7081','monitoring','MediAssist Bengaluru Onco Centre','sensor_failure','E-02','Prakash Bose','2024-05-02','2024-05-13','resolved','Cable harness reseated, fault cleared');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2066','BM-500 Monitor','EQ-MCH-3626','monitoring','MediAssist Mysuru Clinic Hub','calibration_due',NULL,'Myra Desai','2024-02-25',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2067','SterilPro 3000','EQ-BOC-1436','sterilisation','MediAssist Bengaluru Onco Centre','battery_replacement','E-01','Meera Verma','2024-04-27','2024-05-05','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2068','DriveFlow IP-200','EQ-MCH-4678','infusion','MediAssist Mysuru Clinic Hub','preventive_maintenance',NULL,'Vivaan Kumar','2024-04-13','2024-04-15','resolved','Door seal replaced, leak test passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2069','BM-500 Monitor','EQ-PS-8740','monitoring','MediAssist Pune Speciality','fault_reported','E-02','Ishaan Mehta','2024-01-10',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2070','ElectroCautery EC-90','EQ-S-5193','surgical','MediAssist Secunderabad','battery_replacement','S-02','Saanvi Banerjee','2024-02-01',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2071','BM-500 Monitor','EQ-MCH-5720','monitoring','MediAssist Mysuru Clinic Hub','sensor_failure','E-12','Anika Gupta','2024-02-25',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2072','BM-500 Monitor','EQ-HC-8489','monitoring','MediAssist Hyderabad Central','fault_reported','E-07','Arjun Rao','2024-11-26',NULL,'open',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2073','SterilPro 3000','EQ-MCH-3352','sterilisation','MediAssist Mysuru Clinic Hub','sensor_failure','E-01','Kiara Hegde','2024-11-17','2024-11-27','resolved','Cleaned and functional check passed');
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2074','BM-500 Monitor','EQ-MCH-7825','monitoring','MediAssist Mysuru Clinic Hub','preventive_maintenance',NULL,'Diya Krishnan','2024-04-19',NULL,'in_progress',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2075','RadiPro MX-150','EQ-MCH-6908','radiology','MediAssist Mysuru Clinic Hub','sensor_failure','F-09','Arjun Kulkarni','2024-09-17',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2076','RadiPro MX-150','EQ-S-8702','radiology','MediAssist Secunderabad','sensor_failure','F-09','Aditya Murthy','2024-07-12',NULL,'escalated',NULL);
INSERT INTO "maintenance_tickets" VALUES('TKT-2024-2077','DriveFlow IP-200','EQ-PS-2106','infusion','MediAssist Pune Speciality','sensor_failure','F-12','Sneha Menon','2024-12-22',NULL,'escalated',NULL);
COMMIT;
