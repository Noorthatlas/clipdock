def test_linkedin_real_extractor_post_shapes():
    from clipdock.security import normalize

    for url in [
        "https://www.linkedin.com/posts/the-mathworks_2_what-is-mathworks-cloud-center-activity-7151241570371948544-4Gu7",
        "https://www.linkedin.com/posts/mishalkhawaja_sendinblueviews-toronto-digitalmarketing-ugcPost-6850898786781339649-mM20",
    ]:
        assert normalize(url)[1] == "linkedin"
