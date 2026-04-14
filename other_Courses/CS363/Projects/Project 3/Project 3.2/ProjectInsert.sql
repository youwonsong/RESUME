use project3;


LOAD DATA
    INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\user.csv'
    INTO TABLE TwitterUser
    FIELDS TERMINATED BY ';' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (screen_name, name, sub_category, category, ofstate, numFollowers, numFollowing);

LOAD DATA
    INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\tweets.csv'
    INTO TABLE Tweet
    FIELDS TERMINATED BY ';' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (tid, text_body, retweet_count, retweeted, posted, posting_user);
    
LOAD DATA
    INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\urlused.csv'
    INTO TABLE url
    FIELDS TERMINATED BY ';' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (tid, url);
    
LOAD DATA
    INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\tagged.csv'
    INTO TABLE hashtag
    FIELDS TERMINATED BY ';' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (tid, hastagname);
    
LOAD DATA
    INFILE 'C:\\ProgramData\\MySQL\\MySQL Server 8.0\\Uploads\\mentioned.csv'
    INTO TABLE Tweet_mention
    FIELDS TERMINATED BY ';' OPTIONALLY ENCLOSED BY '"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (tid, posting_user);