



Q1	List k=5 most retweeted tweets in a given month = 1 and a given year = 2016; 
show the retweet count, the tweet text, the posting user’s screen name, the posting user’s category, the posting user’s sub-category in descending order of the retweet count values
Rationale: This query finds k most influential tweets in a given time frame and the users who posted them. 

match (t: Tweet)<-[p:POSTED]-(u:User)
where t.month = "1"  AND t.year = "2016"
return t.retweet_count, t.text, u.screen_name, u.category, u.sub_category order by t.retweet_count desc limit 5;

 
Q2	Find k=5 hashtags that appeared in the most number of states in a given year = 2016; list the total number of states the hashtag appeared, 
the list of the distinct states it appeared (FL is the same as Florida*), and the hashtag itself in descending order of the number of states the hashtag appeared.
Rationale: This query finds k hashtags that are used across the most number of states, which could indicate a certain agenda (e.g., education, healthcare) that is widely discussed.
Hint: Use group_concat() function to create a list


Match(U: TwitterUser) - [:tweets] -> [H:hashtag_used]
where U.state !="na" AND T.year_posted = 2016
return H.tag_name, U.state, count(U.state)
order by count(U.state) desc 
limit 5;



*This requires making sure that each state is represented using one name, either FL or Florida, you can use the provided updateStates.sql file to update the states name
Q3	Find k=12 users who used at least one of the hashtags in a given list of hashtags = [HappyNewYear,NewYear,NewYears,NewYearsDay] in their tweets. 
Show the user’s screen name and the state the user lives in descending order of the number of this user’s followers.
 Rationale: This is to find k users with similar interests.

Match(U: TwitterUser) - [:tweets] -> [H:hashtag_used]
where H.tag_name in ('HappyNewYear','NewYear','NewYears','NewYearsDay')
return U.followers, U.screen_name, U.state
order by U.followers desc 
limit 12;

Q4	Find top k=5 most followed users in a given party. Show the user’s screen name, the user’s party, and the number of followers in descending order of the number of followers. 
Show your results with subcategory to be 'GOP' and 'Democrat' separately. 
Rationale: This query finds the most influential users measured by the number of followers


Match(U: TwitterUser)
return U.screen_name, U.sub_category, U.followers
where U.sub_category = "GOP"
order by U.followers desc 
limit 5;


Match(U: TwitterUser)
return screen_name, sub_category, followers
where sub_category = "Democrat"
order by followers desc 
limit 5;


Q5	Find the list of distinct hashtags that appeared in one of the states in a given list = [Ohio, Alaska, Alabama] in a given month = 1 of a given year = 2016; 
show the list of the hashtags and the names of the states in which they appeared. 
Rationale: This is to find interests among the users in the states of interest.

Match(H: hashtag_used) - [:tweets] -> [U:TwitterUser]
return distinct H.tag_name, U.state
where U.state in ("Ohio", "Alaska", "Alabama")
and T.month_posted = 1
and T.year_posted = 2016;

Q6	Find k=5 tweets (with the given hashtag = Ohio) posted by republican (GOP) or democrat members of a given state = Ohio in a given month = 1 of a given year = 2016. 
Show the tweet text, the hashtag, the screen name of the posting user, and the users’ party
Rationale: This query explores the context in which the hashtag was used

Match(T: tweets) - [:hashtag_used] -> [U:TwitterUser]
where H.tag_name = "Ohio"
and U.sub_category in ("GOP", "Democrat")
and T.month_posted = 1
and T.year_posted = 2016
return T.text_body, H.tag_name, U.screen_name, U.sub_category;

Q7	Find users in a given sub-category = ‘GOP’ along with the list of URLs used in the user’s tweets in a given month = 1 of a given year = 2016. 
Show the user’s screen name, the state the user lives, and the list of URLs
Rationale: This query finds URLs shared by a party.

Match(U: TwitterUser) - [:tweets] -> [W:url_used]
where U.sub_category = "GOP"
and T.month_posted = 1
and T.year_posted = 2016
return  U.screen_name, U.state;

Q8	Find k=5 users who were mentioned the most in tweets of users of a given party = ‘GOP’ in a given month = 1 of a given year = 2016. 
Show the user’s screen name, user’s state, 
and the list of the screen name of the user(s) who mentioned this user in descending order of the number of tweets mentioning this user.

Match(U: TwitterUser) - [:tweet_mentions] -> [T:tweets]
return distinct U.screen_name, U.state, group_concat(M.screen_name), count(M.screen_name)
where U.sub_category = "GOP"
and T.month_posted = 1
and T.year_posted = 2016
order by count(M.screen_name) desc 
limit 5;

Q9	Find k=5 most used hashtags with the count of tweets it appeared posted by a given sub-category = ‘GOP’ 
of users in a list of months = [1, 2, 3] of a given year = 2016. Show the hashtag name and the count in descending order of the count.

Match(H: hashtag_used) - [:tweets] -> [U:TwitterUser]
return  H.tag_name, count(H.tag_name)
where U.sub_category = "GOP"
and T.month_posted in (1,2,3)
and T.year_posted = 2016
order by count(H.tag_name) desc 
limit 5;