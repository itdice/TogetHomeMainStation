/*
mainstationDBcreation.sql
Toget Home Main Station Server

Created by IT DICE on 2023/04/30.
*/
create table Home
(
    Home_name     varchar(32) not null
        primary key,
    Interval_time int         null,
    Expire_count  int         null
)
    comment 'Home Data';

create table Router
(
    ID   binary(6)   not null
        primary key,
    SSID varchar(32) not null,
    MAC  binary(6)   not null
)
    comment 'Wi-Fi Access Point Data';

create table Space
(
    ID            binary(6)   not null
        primary key,
    Familiar_name varchar(32) null,
    Size_X        float       not null,
    Size_Y        float       not null
)
    comment 'Home Space Data';

create table Beacon
(
    ID        binary(6)  not null
        primary key,
    State     binary(2)  not null,
    SpaceID   binary(6)  not null,
    Pos_X     float      not null,
    Pos_Y     float      not null,
    Power     int        null,
    isPrimary tinyint(1) not null,
    constraint Beacon_Space_ID_fk
        foreign key (SpaceID) references Space (ID)
            on delete cascade
)
    comment 'Toget Home Beacon Data';

create table PRI_Beacon
(
    BeaconID binary(6) not null,
    SpaceID  binary(6) not null,
    Min_RSSI int       null,
    Max_RSSI int       null,
    primary key (BeaconID, SpaceID),
    constraint PRI_Beacon_Beacon_ID_fk
        foreign key (BeaconID) references Beacon (ID)
            on delete cascade,
    constraint PRI_Beacon_Space_ID_fk
        foreign key (SpaceID) references Space (ID)
            on delete cascade
)
    comment 'Primary Beacon RSSI Data';

create table PRI_Router
(
    RouterID binary(6) not null,
    SpaceID  binary(6) not null,
    Min_RSSI int       null,
    Max_RSSI int       null,
    primary key (RouterID, SpaceID),
    constraint PRI_Router_Router_ID_fk
        foreign key (RouterID) references Router (ID)
            on delete cascade,
    constraint PRI_Router_Space_ID_fk
        foreign key (SpaceID) references Space (ID)
            on delete cascade
)
    comment 'Primary Router RSSI Data';

create table User
(
    ID        binary(6)   not null
        primary key,
    User_name varchar(32) null
)
    comment 'IPS User Data';

create table Device
(
    ID            binary(6)   not null
        primary key,
    Familiar_name varchar(32) null,
    State         binary(2)   not null,
    UserID        binary(6)   not null,
    constraint Device_User_ID_fk
        foreign key (UserID) references User (ID)
            on delete cascade
)
    comment 'Client Device Data';

create table Pos_Data
(
    DeviceID  binary(6)                             not null
        primary key,
    SpaceID   binary(6)                             null,
    Pos_X     float                                 null,
    Pos_Y     float                                 null,
    Data_time timestamp default current_timestamp() not null on update current_timestamp(),
    constraint Pos_Data_Device_ID_fk
        foreign key (DeviceID) references Device (ID)
            on delete cascade,
    constraint Pos_Data_Space_ID_fk
        foreign key (SpaceID) references Space (ID)
            on delete cascade
)
    comment 'Device Position Data';

