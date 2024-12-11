-- remote apis
INSERT INTO client_details (id,clientId,clientSecret,token_validity,refresh_validity,createdDate,modifiedDate) VALUES (1,"sequencerClient","sequencerClientSecret",100000,2592000,now(),now());
INSERT INTO client_details_grant_types (client_details_id,grant_value) VALUES (1,"password");
INSERT INTO client_details_scope (client_details_id,scope) VALUES (1,"read");
INSERT INTO client_details_scope (client_details_id,scope) VALUES (1,"write");
-- user -- password encryption of `password1`
INSERT INTO user (`createdDate`, `modifiedDate`, `email`, `firstName`, `lastName`, `locale`, `password`, `phoneNumber`, `username`, `enabled`, `system_role`, `credentialsNonExpired`, `user_type`) VALUES (now(), now() , 'jeffrey.thiessen@phac-aspc.gc.ca', 'Jeffrey', 'Thiessen', 'en', '$2a$10$yvzFLxWA9m2wNQmHpJtWT.MRZv8qV8Mo3EMB6HTkDnUbi9aBrbWWW', '0000', 'jeff', 1, 'ROLE_ADMIN', 1, 'TYPE_LOCAL');
