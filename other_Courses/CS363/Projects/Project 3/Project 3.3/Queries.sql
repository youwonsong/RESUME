use project3;


select T.retweet_count, T.text_body, T.posting_user,
U.category, U.sub_category from Tweets T
inner join TwitterUser U
on U.screen_name = T.posting_user
and T.month_posted = 1 and T.year_posted = 2016
order by T.retweet_count desc limit 5; 
 

select distinct H.tag_name, count(U.state), U.state
from TwitterUser U
inner join tweets T on T.posting_user = U.screen_name
inner join hashtag_used H on H.tweet_id = T.tweet_id
and T.year_posted = 2016
and U.state != "na"
group by H.tag_name, U.state
order by count(U.state) desc limit 5;


select U.followers, U.screen_name, U.state
from TwitterUser U
inner join Tweets T
on U.screen_name = T.posting_user
inner join hashtag_used H
on H.tweet_id = T.tweet_id
where H.tag_name in ('HappyNewYear','NewYear','NewYears','NewYearsDay')
group by U.followers, U.screen_name
order by U.followers desc limit 12;

#Q4, 2 queries.
select U.screen_name, U.sub_category, U.followers
from TwitterUser U
where U.sub_category = "GOP"
order by U.followers desc limit 5;

select screen_name, sub_category, followers
from TwitterUser
where sub_category = "Democrat"
order by followers desc limit 5;



select distinct H.tag_name, U.state
from hashtag_used H
inner join tweets T on H.tweet_id = T.tweet_id
inner join TwitterUser U on T.posting_user = U.screen_name
where U.state in ("Ohio", "Alaska", "Alabama")
and T.month_posted = 1
and T.year_posted = 2016;


select T.text_body, H.tag_name, U.screen_name, U.sub_category
from tweets T
inner join hashtag_used H on H.tweet_id = T.tweet_id
inner join TwitterUser U on T.posting_user = U.screen_name
where H.tag_name = "Ohio"
and U.sub_category in ("GOP", "Democrat")
and T.month_posted = 1
and T.year_posted = 2016;


select distinct U.screen_name, U.state, group_concat(W.url)
from TwitterUser U
inner join tweets T on T.posting_user = U.screen_name
inner join url_used W on W.tweet_id = T.tweet_id
where U.sub_category = "GOP"
and T.month_posted = 1
and T.year_posted = 2016
group by U.screen_name, U.state ;


select distinct U.screen_name, U.state, group_concat(M.screen_name), count(M.screen_name)
from TwitterUser U
inner join tweet_mentions M on M.screen_name = U.screen_name
inner join tweets T on T.posting_user = U.screen_name
where U.sub_category = "GOP"
and T.month_posted = 1
and T.year_posted = 2016
group by U.screen_name, U.state
order by count(M.screen_name) desc limit 5;


select H.tag_name, count(H.tag_name)
from hashtag_used H
inner join tweets T on H.tweet_id = T.tweet_id
inner join TwitterUser U on U.screen_name = T.posting_user
and U.sub_category = "GOP"
and T.month_posted in (1,2,3)
and T.year_posted = 2016
group by H.tag_name
order by count(H.tag_name) desc limit 5;