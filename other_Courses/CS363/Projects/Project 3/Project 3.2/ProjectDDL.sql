
drop database if exists project3;
create database project3;
use project3;
set global local_infile = 'ON';

CREATE TABLE IF NOT EXISTS TwitterUser (
    screen_name varchar(30),
    numFollowing int,
    numFollowers int,
    name varchar(30),
    sub_category varchar(20),
    category varchar(35),
    ofstate varchar(30),
    constraint chk_category check(category in ('senate_group','presidential_candidate','reporter','Senator','House_representative','General',NULL)),
    constraint chk_sub_category check(sub_category in ('GOP','Democrat','na',NULL)),
    primary key(screen_name)
);

CREATE TABLE IF NOT EXISTS Tweet (
	tid bigint,
    posting_user varchar(30) not null,
    posted datetime,
    retweet_count int,
    retweeted int,
    text_body varchar(300),
    primary key(tid,posting_user),
    foreign key(posting_user) references TwitterUser(screen_name) on delete cascade
); 

CREATE TABLE IF NOT EXISTS hashtag (
	hastagname varchar(50),
    tid bigint not null,
	primary key(hastagname,tid),
    foreign key(tid) references Tweet(tid) on delete cascade
);

CREATE TABLE IF NOT EXISTS url (
	url varchar(600),
	tid bigint not null,
    primary key(url,tid),
    foreign key(tid) references Tweet(tid) on delete cascade
);

CREATE TABLE IF NOT EXISTS Tweet_mention (
	posting_user varchar(30),
	tid bigint not null,
    primary key(posting_user,tid),
    foreign key(tid) references Tweet(tid) on delete cascade,
	foreign key(posting_user) references TwitterUser(screen_name) on delete cascade
);